import json

from .tools import sanitize


COMMANDS={'start':'Bắt đầu hoặc xem numeric User ID','help':'Các lệnh được hỗ trợ','status':'Trạng thái thực từ Gateway',
          'projects':'Project đã cấu hình và được phép','tasks':'Danh sách Task','active':'Agent và Task hiện tại',
          'blocked':'Task bị chặn','notifications':'Bật/tắt thông báo','settings':'Xem/chọn project','cancel':'Hủy xác nhận đang chờ'}


def chunks(text):return [text[index:index+3800] for index in range(0,len(text),3800)] or ['Không có dữ liệu.']
def render(value):return json.dumps(sanitize(value),ensure_ascii=False,indent=2)


def create_dispatcher(repo,settings,gateway,commander,health):
    from aiogram import Dispatcher,BaseMiddleware
    from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton

    dispatcher=Dispatcher()

    class Once(BaseMiddleware):
        async def __call__(self,handler,event,data):
            if not repo.claim_update(event.update_id):return None
            return await handler(event,data)
    dispatcher.update.outer_middleware(Once())

    async def send(message,text,confirmation_id=None):
        keyboard=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Xác nhận',callback_data='confirm:'+confirmation_id),
            InlineKeyboardButton(text='Hủy',callback_data='cancel:'+confirmation_id)]]) if confirmation_id else None
        for index,part in enumerate(chunks(text)):
            sent=await message.answer(part,reply_markup=keyboard if index==0 else None)
            repo.audit(message.chat.id,message.chat.id,{'event':'BOT_REPLY_SENT','message_id':sent.message_id,
                'in_reply_to_message_id':message.message_id,'part':index+1})

    def scope(user,chat):
        pair=repo.authorize(user,chat)
        if not pair:raise PermissionError('TELEGRAM_NOT_PAIRED')
        available=[p for p in pair['project_ids'] if p in settings.project_ids]
        if not available:raise PermissionError('PROJECT_ACCESS_REVOKED')
        memory=repo.memory(user,chat)
        return pair,memory['current_project_id'] if memory.get('current_project_id') in available else available[0]

    @dispatcher.message()
    async def message_handler(message):
        if message.chat.type!='private' or not message.from_user or message.from_user.is_bot:return
        user,chat=message.from_user.id,message.chat.id
        if not repo.rate_limit(user,settings.rate_limit_per_minute):
            await send(message,'Đã chạm giới hạn yêu cầu trong phút này. Vui lòng thử lại sau.');return
        text=(message.text or '').strip()
        command,_,argument=text.partition(' ')
        command=command.split('@',1)[0]
        if command=='/start':
            if argument:
                await send(message,'Ghép nối thành công.' if repo.pair(argument,user,chat) else 'Mã ghép nối không hợp lệ, hết hạn hoặc đã sử dụng.')
            elif repo.authorize(user,chat):await send(message,'QLDAPM AI Commander đã sẵn sàng. Dùng /help hoặc hỏi về Task.')
            else:await send(message,f'Tài khoản chưa kích hoạt. Numeric User ID: {user}. Tạo mã trên máy quản trị rồi gửi /pair <mã>. Không gửi API key vào bot.')
            return
        if command=='/pair':
            await send(message,'Ghép nối thành công.' if repo.pair(argument,user,chat) else 'Mã ghép nối không hợp lệ, hết hạn hoặc đã sử dụng.');return
        try:
            pair,project=scope(user,chat)
            if command=='/help':
                await send(message,'\n'.join('/'+name+' — '+description for name,description in COMMANDS.items())+'\nCó thể hỏi tiếng Việt về Task/Run. Thao tác ghi luôn cần nút xác nhận riêng.');return
            if command=='/cancel':
                repo.cancel_pending(user,chat);await send(message,'Đã hủy xác nhận đang chờ. Lệnh đã được Gateway nhận trước đó không bị hủy bởi /cancel.');return
            if command=='/settings':
                if argument:
                    chosen=int(argument)
                    if chosen not in pair['project_ids'] or chosen not in settings.project_ids:raise PermissionError('PROJECT_NOT_ALLOWED')
                    memory=repo.memory(user,chat);memory.update(current_project_id=chosen,current_task_id=None,current_run_id=None)
                    repo.save_memory(user,chat,memory);project=chosen
                await send(message,render({'project_id':project,'project_ids':pair['project_ids'],'model':settings.gemini_model,
                    'gemini':health.get('gemini'),'notice':'Chọn project bằng /settings <ID>. Không nhập secret ở đây.'}));return
            if command=='/notifications':
                if argument in {'on','off'}:repo.set_notifications(user,argument=='on')
                if argument.startswith('types '):repo.set_notification_types(user,[v.strip() for v in argument[6:].split(',') if v.strip()])
                updated=repo.authorize(user,chat)
                await send(message,render({'enabled':bool(updated['notifications']),
                    'types':json.loads(updated['notification_types']) if updated.get('notification_types') is not None else 'ALL_REQUIRED_TYPES',
                    'usage':'/notifications on|off; /notifications types TASK_COMPLETED,TASK_BLOCKED,AGENT_FAILED,QA_FAILED,AWAITING_APPROVAL,PR_CREATED',
                    'delivery':health.get('notifications','NOT_VERIFIED')}));return
            if command=='/projects':value=await commander.tools.execute('list_projects',{},user,chat,project)
            elif command=='/tasks':value=await commander.tools.execute('search_tasks',{'query':argument},user,chat,project)
            elif command in {'/active','/blocked','/status'}:
                value=await gateway.command('observer_active',{'summary_only':True} if command=='/status' else {},project)
                if command=='/blocked':
                    rows=value.get('tasks') or value.get('items') or []
                    value={'project_id':project,'tasks':[row for row in rows if row.get('workflow_status') in {'BLOCKED','FAILED'}
                        or any(s.get('status') in {'BLOCKED','FAILED'} for s in row.get('stages',[]))],
                        'notice':'Chỉ các Task có dữ liệu Observer trong snapshot; không suy luận từ AUTO.'}
                elif command=='/status':value={'service':health,'observer':value}
            elif command.startswith('/'):
                await send(message,'Lệnh chưa được hỗ trợ. Dùng /help.');return
            else:
                if not text:await send(message,'Hiện hỗ trợ tin nhắn văn bản.');return
                context=repo.notification_context(chat,message.reply_to_message.message_id) if message.reply_to_message else None
                if context and context['project_id'] not in pair['project_ids']:raise PermissionError('REPLY_PROJECT_NOT_ALLOWED')
                repo.audit(user,chat,{'event':'INCOMING_CONTEXT','message_id':message.message_id,
                    'reply_to_message_id':message.reply_to_message.message_id if message.reply_to_message else None,
                    'notification_context':context,'conversation_task_id':repo.memory(user,chat).get('current_task_id')})
                response=await commander.answer(user,chat,text,project,reply_context=context)
                await send(message,response['text'],response.get('confirmation_id'));return
            await send(message,render(value))
        except Exception as error:
            repo.audit(user,chat,{'event':'MESSAGE_REJECTED','error_type':type(error).__name__})
            await send(message,'Hiện tôi chưa xác minh được trạng thái này từ hệ thống. '+
                ('Tài khoản chưa được ghép nối hoặc không có quyền project.' if isinstance(error,PermissionError)
                 else 'Gateway chưa sẵn sàng hoặc tham số chưa hợp lệ; không tự retry lệnh ghi.'))

    @dispatcher.callback_query()
    async def callback_handler(callback):
        if not callback.message or callback.message.chat.type!='private' or not callback.from_user:return
        user,chat=callback.from_user.id,callback.message.chat.id
        try:
            scope(user,chat)
            action,nonce=(callback.data or '').split(':',1)
            if action=='cancel':
                # A stale cancel must not consume a newer pending confirmation.
                memory=repo.memory(user,chat)
                if memory.get('pending_confirmation')!=nonce:raise ValueError('CONFIRMATION_EXPIRED')
                repo.cancel_pending(user,chat);await callback.answer('Đã hủy.');return
            if action!='confirm':raise ValueError('CALLBACK_NOT_ALLOWED')
            await callback.answer('Đang kiểm tra lại trạng thái và quyền...')
            result=await commander.tools.confirm(nonce,user,chat)
            await send(callback.message,render(result),result.get('confirmation_id'))
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as error:
            repo.audit(user,chat,{'event':'CALLBACK_REJECTED','error_type':type(error).__name__})
            await callback.answer('Xác nhận hết hạn/đã dùng, trạng thái đổi hoặc Gateway từ chối.',show_alert=True)

    return dispatcher
