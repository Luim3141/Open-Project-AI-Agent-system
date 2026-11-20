import argparse
import asyncio
import contextlib
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path

from .config import Settings
from .storage import Repository
from .gateway import GatewayClient


def process_lock(path):
    handle=open(path,'a+')
    try:
        if os.name=='nt':
            import msvcrt
            handle.seek(0);handle.write('0');handle.flush();handle.seek(0)
            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        handle.close();raise RuntimeError('ANOTHER_POLLING_CONSUMER_IS_RUNNING') from None
    return handle


async def serve():
    from aiohttp import web
    from aiogram import Bot
    from aiogram.types import BotCommand
    from aiogram.utils.backoff import BackoffConfig
    from .engine import GeminiBrain,Commander
    from .tools import ToolExecutor
    from .handlers import create_dispatcher,COMMANDS
    from .notifications import create_app
    settings=Settings.from_env();repo=Repository(settings.db_path)
    lock=process_lock(settings.db_path.parent/'polling.lock')
    gateway=GatewayClient(settings);brain=GeminiBrain(settings,repo)
    health={'state':'STARTING','telegram':'NOT_VERIFIED','gateway':'NOT_VERIFIED',
            'gemini':'CONFIGURED_UNVERIFIED' if settings.gemini_api_key else 'MISSING_KEY',
            'notifications':'NOT_VERIFIED','updated_at':time.time()}
    app=create_app(repo,settings,gateway)
    async def status(request):
        now=time.time()
        if brain.last_verified_at:
            health.update(gemini='READY' if now-brain.last_verified_at<=300 else 'READINESS_STALE',
                          gemini_last_verified_at=brain.last_verified_at)
        with repo.connect() as db:
            counts=dict(db.execute('SELECT status,count(*) FROM telegram_notification_outbox GROUP BY status').fetchall())
        health['notifications']={'state':'DELIVERY_VERIFIED' if counts.get('SENT') else 'NO_DELIVERY_VERIFIED','outbox':counts}
        try:
            response=await gateway.client.get('/health',timeout=2)
            health['gateway']={'state':'REACHABLE' if response.status_code==200 else 'UNAVAILABLE','check':'HTTP_HEALTH_ONLY'}
        except Exception:health['gateway']={'state':'UNREACHABLE','check':'HTTP_HEALTH_ONLY'}
        return web.json_response({**health,'updated_at':now})
    app.router.add_get('/health',status)
    runner=web.AppRunner(app);await runner.setup();await web.TCPSite(runner,'0.0.0.0',8091).start()
    stop=asyncio.Event();loop=asyncio.get_running_loop()
    for sig in (signal.SIGINT,signal.SIGTERM):
        try:loop.add_signal_handler(sig,stop.set)
        except NotImplementedError:pass
    bot=None;polling=None;delay=2
    try:
        while not stop.is_set():
            missing=settings.missing()
            if missing:
                health.update(state='WAITING_CONFIGURATION',missing=missing)
                try:await asyncio.wait_for(stop.wait(),10)
                except TimeoutError:pass
                continue
            if not settings.polling_enabled:
                health.update(state='POLLING_DISABLED');await stop.wait();break
            try:
                bot=Bot(settings.bot_token)
                identity=await bot.get_me()
                health['telegram']='CONNECTED';health['bot_username']=identity.username
                hook=await bot.get_webhook_info()
                if hook.url:
                    if not settings.allow_webhook_removal:
                        health.update(state='BLOCKED_EXISTING_WEBHOOK');await stop.wait();break
                    await bot.delete_webhook(drop_pending_updates=False)
                await gateway.command('identity',{},settings.project_ids[0]);health['gateway']='CONNECTED'
                health.update(state='POLLING',missing=[])
                await bot.set_my_commands([BotCommand(command=name,description=description) for name,description in COMMANDS.items()])
                commander=Commander(settings,repo,ToolExecutor(gateway,repo,settings),brain)
                dispatcher=create_dispatcher(repo,settings,gateway,commander,health)
                polling=asyncio.create_task(dispatcher.start_polling(bot,handle_as_tasks=False,handle_signals=False,
                    close_bot_session=False,backoff_config=BackoffConfig(min_delay=2,max_delay=60,factor=1.8,jitter=.2)))
                stopped=asyncio.create_task(stop.wait())
                done,_=await asyncio.wait([polling,stopped],return_when=asyncio.FIRST_COMPLETED)
                if stopped in done:
                    if not polling.done():await dispatcher.stop_polling()
                    await polling;break
                stopped.cancel()
                await polling
            except Exception as error:
                health.update(state='RETRY_WAIT',last_error_type=type(error).__name__)
                logging.getLogger(__name__).warning('Connection unavailable: %s',type(error).__name__)
                try:await asyncio.wait_for(stop.wait(),delay)
                except TimeoutError:pass
                delay=min(delay*2,60)
            finally:
                if bot:await bot.session.close();bot=None
    finally:
        health['state']='STOPPED'
        if polling and not polling.done():polling.cancel()
        await brain.close();await gateway.close();await runner.cleanup();lock.close()


async def check_connections(settings,provider_probe=False):
    from aiogram import Bot
    result={'missing':settings.missing(),'model':settings.gemini_model,'inference':'NOT_RUN'}
    if settings.bot_token:
        bot=Bot(settings.bot_token)
        try:
            me=await bot.get_me();hook=await bot.get_webhook_info()
            result.update(telegram='CONNECTED',bot_username=me.username,webhook_configured=bool(hook.url))
        except Exception as error:result['telegram']=type(error).__name__
        finally:await bot.session.close()
    gateway=GatewayClient(settings)
    try:
        result['projects']=[]
        for project in settings.project_ids:
            try:
                identity=await gateway.command('identity',{},project)
                result['projects'].append({'project_id':project,'state':'VERIFIED','actor_id':identity.get('user_id') or identity.get('id')})
            except Exception as error:result['projects'].append({'project_id':project,'error_type':type(error).__name__})
    finally:await gateway.close()
    if settings.gemini_api_key:
        from google import genai
        from google.genai import types
        client=genai.Client(api_key=settings.gemini_api_key,http_options=types.HttpOptions(timeout=15000,retry_options=types.HttpRetryOptions(attempts=1)))
        try:
            model=await client.aio.models.get(model=settings.gemini_model)
            result['gemini_model_access']='VERIFIED';result['resolved_model']=model.name
            if provider_probe:
                if not settings.provider_data_consent:raise PermissionError('GEMINI_PROJECT_DATA_CONSENT_REQUIRED')
                from .engine import GeminiBrain
                brain=GeminiBrain(settings,Repository(settings.db_path))
                try:
                    probe=await brain.generate([{'role':'user','parts':[{'text':'Gọi get_system_health để kiểm tra công cụ. Chỉ dùng function call.'}]}],
                        [{'name':'get_system_health','description':'Kiểm tra tình trạng','parameters':{'type':'object','properties':{}}}])
                    result['inference']='FUNCTION_CALL_VERIFIED' if any(c['name']=='get_system_health' for c in probe['calls']) else 'FUNCTION_CALL_NOT_RETURNED'
                finally:await brain.close()
        except Exception as error:result['gemini_error_type']=type(error).__name__
        finally:await client.aio.aclose();client.close()
    return result


async def delivery_test(settings,user_id,project_id,task_id):
    import uuid
    from .notifications import Outbox
    repo=Repository(settings.db_path)
    person=next((p for p in repo.recipients() if p['user_id']==user_id and project_id in p['project_ids']),None)
    if not person:raise PermissionError('PAIRED_NOTIFICATION_RECIPIENT_REQUIRED')
    client=GatewayClient(settings)
    try:snapshot=await client.command('observer_task_progress',{'task_id':task_id},project_id)
    finally:await client.close()
    if snapshot.get('task_id')!=task_id or snapshot.get('project_id')!=project_id:raise ValueError('EXACT_TASK_READBACK_REQUIRED')
    identifier='delivery-test:'+uuid.uuid4().hex
    event={'event_id':identifier,'event_type':'DELIVERY_TEST','task_id':task_id,'project_id':project_id,
        'workflow_run_id':snapshot.get('latest_run_id'),'source_record_id':'LOCAL_OPERATOR_CHECK:'+identifier,'timestamp':time.time()}
    repo.audit(user_id,user_id,{'event':'DELIVERY_SELF_CHECK','event_id':identifier,'task_id':task_id,
        'project_id':project_id,'task_revision':snapshot.get('revision')})
    if not Outbox(repo).enqueue(event,person):raise ValueError('NOTIFICATION_PREFERENCE_DENIED')
    return {'state':'QUEUED','event_id':identifier,'event_type':'DELIVERY_TEST','business_writes':0,'task_id':task_id}


def main():
    parser=argparse.ArgumentParser(description='QLDAPM Telegram local administration; never paste keys in chat.')
    sub=parser.add_subparsers(dest='operation')
    pair=sub.add_parser('pair');pair.add_argument('--user-id',type=int,required=True);pair.add_argument('--projects',required=True)
    revoke=sub.add_parser('revoke');revoke.add_argument('--user-id',type=int,required=True)
    check=sub.add_parser('check');check.add_argument('--provider-probe',action='store_true')
    notify=sub.add_parser('notify-test');notify.add_argument('--user-id',type=int,required=True)
    notify.add_argument('--project-id',type=int,required=True);notify.add_argument('--task-id',type=int,required=True)
    sub.add_parser('health')
    args=parser.parse_args();settings=Settings.from_env()
    if args.operation=='pair':
        projects=[int(p.strip()) for p in args.projects.split(',')]
        if any(p not in settings.project_ids for p in projects):parser.error('Project is not in QLDAPM_ALLOWED_PROJECT_IDS')
        code=Repository(settings.db_path).create_pairing(args.user_id,projects)
        print('Mã ghép nối dùng một lần trong 5 phút (không chia sẻ): '+code)
        print('Gửi /pair <mã> trong private chat của bot.');return
    if args.operation=='revoke':Repository(settings.db_path).revoke(args.user_id);print('Đã thu hồi quyền.');return
    if args.operation=='check':print(json.dumps(asyncio.run(check_connections(settings,args.provider_probe)),ensure_ascii=False,indent=2));return
    if args.operation=='notify-test':print(json.dumps(asyncio.run(delivery_test(settings,args.user_id,args.project_id,args.task_id))));return
    if args.operation=='health':
        import urllib.request
        with urllib.request.urlopen('http://127.0.0.1:8091/health',timeout=3) as response:print(response.read().decode())
        return
    logging.basicConfig(level=logging.WARNING,format='%(levelname)s %(message)s')
    # Client debug logs can contain credential-bearing Telegram API URLs.
    for name in ('httpx','httpcore','aiogram','google.genai'):logging.getLogger(name).setLevel(logging.CRITICAL)
    asyncio.run(serve())


if __name__=='__main__':main()
