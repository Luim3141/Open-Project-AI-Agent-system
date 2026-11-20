import asyncio
import json
import re
import time
import uuid

from .system_instructions import SYSTEM_INSTRUCTIONS
from .tools import declarations,sanitize,context_result,WRITES
from .gateway import GatewayError


def knowledge_references(value):
    references=[]
    for item in value.get('items',[])[:5]:
        uri=item.get('citation','')
        valid_file=isinstance(uri,str) and re.fullmatch(r'file:[a-z0-9][a-z0-9_-]{0,63}#sha256=[a-f0-9]{64}',uri)
        valid_native=type(item.get('native_id')) is int and item['native_id']>0 and type(item.get('lock_version')) is int and uri==f"/work_packages/{item['native_id']}"
        if valid_file or valid_native:
            reference=uri+(f" · Native version {item['lock_version']}" if valid_native else '')
            if reference not in references and len(references)<3:references.append(reference)
    return references


class GeminiBrain:
    def __init__(self,settings,repo):
        self.settings,self.repo=settings,repo
        self.client=None;self.model_mismatch=False;self.last_verified_at=None

    async def generate(self,contents,functions):
        if not self.settings.gemini_api_key:raise ValueError('GEMINI_API_KEY_MISSING')
        if self.model_mismatch:raise ValueError('GEMINI_MODEL_ROUTING_MISMATCH_LOCKED')
        if not self.settings.provider_data_consent:raise PermissionError('GEMINI_PROJECT_DATA_CONSENT_REQUIRED')
        from google import genai
        from google.genai import types
        if self.client is None:
            self.client=genai.Client(api_key=self.settings.gemini_api_key,http_options=types.HttpOptions(
                timeout=30000,retry_options=types.HttpRetryOptions(attempts=1)))
        for attempt in range(2):
            self.repo.reserve_model_call(self.settings.max_daily_model_calls)
            started=time.monotonic();response=None;failure=None;error_type=None
            try:
                response=await self.client.aio.models.generate_content(model=self.settings.gemini_model,contents=contents,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTIONS,
                        tools=[types.Tool(function_declarations=functions)] if functions else None,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                        max_output_tokens=self.settings.max_output_tokens))
            except asyncio.CancelledError:
                error_type='CancelledError';raise
            except Exception as error:
                failure=error;error_type=type(error).__name__
            finally:
                usage=getattr(response,'usage_metadata',None)
                self.repo.audit(0,0,{'event':'GEMINI_REQUEST','request_id':uuid.uuid4().hex,'model_id':self.settings.gemini_model,
                    'resolved_model_version':getattr(response,'model_version',None),
                    'input_tokens':getattr(usage,'prompt_token_count',None),'output_tokens':getattr(usage,'candidates_token_count',None),
                    'tool_calls_count':len(getattr(response,'function_calls',None) or []),'attempt':attempt+1,
                    'http_status':getattr(failure,'code',None),
                    'latency_seconds':round(time.monotonic()-started,3),'error_type':error_type})
            if failure:
                code=getattr(failure,'code',None)
                if attempt==0 and type(code) is int and 500<=code<600:
                    await asyncio.sleep(2);continue
                raise failure
            break
        actual=getattr(response,'model_version',None)
        if actual and actual!=self.settings.gemini_model and not actual.startswith(self.settings.gemini_model+'-'):
            self.model_mismatch=True
            raise ValueError('GEMINI_MODEL_ROUTING_MISMATCH')
        self.last_verified_at=time.time()
        content=response.candidates[0].content if response.candidates else None
        calls=[{'name':call.name,'args':dict(call.args or {}),**({'id':call.id} if getattr(call,'id',None) else {})} for call in response.function_calls or []]
        text=''.join(part.text for part in content.parts or [] if part.text and not part.thought) if content else ''
        return {'content':content,'calls':calls,'text':text}

    async def close(self):
        if self.client:
            await self.client.aio.aclose()
            self.client.close()


class Commander:
    def __init__(self,settings,repo,tools,brain):self.settings,self.repo,self.tools,self.brain=settings,repo,tools,brain

    async def answer(self,user_id,chat_id,text,project_id,reply_context=None):
        try:
            async with asyncio.timeout(self.settings.request_timeout_seconds):
                return await self._answer(user_id,chat_id,sanitize(text[:8000]),project_id,reply_context)
        except Exception as error:
            self.repo.audit(user_id,chat_id,{'event':'AI_REQUEST_FAILED','error_type':type(error).__name__,
                'error_code':str(error)[:160] if isinstance(error,GatewayError) else type(error).__name__})
            return {'text':'Hiện tôi chưa xác minh được trạng thái này từ hệ thống. Gemini hoặc Gateway chưa sẵn sàng; xem /status. Không có lệnh nào được tự động chạy lại.'}

    async def _answer(self,user_id,chat_id,text,project_id,reply_context):
        memory=self.repo.memory(user_id,chat_id)
        if reply_context:
            memory.update(current_project_id=reply_context['project_id'],current_task_id=reply_context['task_id'],current_run_id=reply_context.get('run_id'))
            project_id=reply_context['project_id']
        explicit=re.search(r'(?:task|wp|#)\s*#?\s*(\d+)',text,re.I)
        if explicit:memory.update(current_task_id=int(explicit[1]),current_project_id=project_id)
        self.repo.save_memory(user_id,chat_id,memory)
        self.repo.append_message(user_id,chat_id,'user',text)
        context={'project_id':project_id,'current_task_id':memory.get('current_task_id'),'current_run_id':memory.get('current_run_id'),
                 'constraints':memory.get('constraints',[]),'historical_summary':memory.get('summary','')}
        live=None
        if memory.get('current_task_id'):
            try:live=await self.tools.execute('get_task_progress',{'task_id':memory['current_task_id']},user_id,chat_id,project_id)
            except GatewayError as error:
                if not str(error).startswith(('GATEWAY_HTTP_403','GATEWAY_HTTP_404')) or re.search(r'(?:project|dự án)\s*#?\s*\d+',text,re.I):raise
                pair=self.repo.authorize(user_id,chat_id)
                candidates=[p for p in (pair or {}).get('project_ids',[]) if p in self.settings.project_ids and p!=project_id]
                for candidate in candidates:
                    try:live=await self.tools.execute('get_task_progress',{'task_id':memory['current_task_id']},user_id,chat_id,candidate)
                    except GatewayError as other:
                        if not str(other).startswith(('GATEWAY_HTTP_403','GATEWAY_HTTP_404')):raise
                        continue
                    project_id=candidate;break
                if live is None:raise
            current=self.repo.memory(user_id,chat_id);current['current_project_id']=project_id
            self.repo.save_memory(user_id,chat_id,current)
            context.update(project_id=project_id,current_run_id=current.get('current_run_id'))
        elif re.search(r'trạng thái|tiến độ|đang|hoạt động|agent|blocked|hệ thống|task|dự án',text,re.I):
            live=await self.tools.execute('get_system_health',{},user_id,chat_id,project_id)
        context['verified_this_turn']=context_result(live)
        knowledge_turn=bool(re.search(r'tài liệu|tri thức|\b(?:documents?|documentation|knowledge|rag)\b',text,re.I))
        knowledge_citations=[]
        if knowledge_turn:
            async with asyncio.timeout(self.settings.tool_timeout_seconds):
                evidence=await self.tools.execute('search_knowledge',{'query':text[:500],'mode':'answer'},user_id,chat_id,project_id)
            if not evidence.get('items'):
                label='SEARCH_UNAVAILABLE' if evidence.get('search_status')=='DEGRADED_ERROR' else 'NO_EVIDENCE'
                result=label+' — Chưa có nguồn hiện hành để xác nhận; không dùng câu trả lời cũ trong memory để xác nhận tài liệu.'
                self.repo.append_message(user_id,chat_id,'model',result)
                return {'text':result}
            context['verified_knowledge']=context_result(evidence)
            knowledge_citations=knowledge_references(evidence)
        contents=[]
        for item in memory.get('recent_messages',[])[-12:]:
            contents.append({'role':'model' if item['role']=='model' else 'user','parts':[{'text':item['text'][:3000]}]})
        contents.append({'role':'user','parts':[{'text':json.dumps(context,ensure_ascii=False)[:22000]+'\nYêu cầu hiện tại: '+text}]})
        calls_used=1 if knowledge_turn else 0;verified=['search_knowledge'] if knowledge_turn else []
        for _ in range(self.settings.max_tool_rounds):
            if len(str(contents))>64000:break
            functions=[f for f in declarations() if not knowledge_turn or f['name'] not in WRITES]
            response=await self.brain.generate(contents,functions)
            calls=response['calls']
            knowledge_turn=knowledge_turn or any(c['name']=='search_knowledge' for c in calls)
            if not calls:
                result=sanitize(response['text']) or 'Hiện tôi chưa xác minh được trạng thái này từ hệ thống.'
                if re.search(r'\bDONE\b',text+' '+result,re.I):
                    current=self.repo.memory(user_id,chat_id).get('current_task_id')
                    snapshot=live if isinstance(live,dict) and live.get('task_id')==current else {}
                    if current:
                        # DONE is a Native acceptance verdict, never a model's synonym for runtime success.
                        complete=snapshot.get('business_status')=='DONE' and snapshot.get('acceptance_status')=='FULLY_COMPLETED' and not snapshot.get('source_conflicts')
                        result=(f'Task #{current} '+('đã được xác nhận DONE.' if complete else 'chưa được xác nhận DONE.')+
                            '\nRuntime: '+str(snapshot.get('workflow_status','NOT_RECORDED'))+
                            '\nBusiness: '+str(snapshot.get('business_status','NOT_RECORDED'))+
                            '\nAcceptance: '+str(snapshot.get('acceptance_status','NOT_RECORDED'))+
                            '\nNguồn: Observer/Native acceptance của lượt hỏi hiện tại.')
                        self.repo.audit(user_id,chat_id,{'event':'ACCEPTANCE_ANSWER_GROUNDED','task_id':current,
                            'acceptance_status':snapshot.get('acceptance_status'),'complete':complete})
                if knowledge_citations and not re.search(r'\bDONE\b',text+' '+result,re.I):
                    result+='\n\nNguồn truy hồi đã đối chiếu (không phải xác nhận runtime):\n'+'\n'.join(knowledge_citations)
                self.repo.append_message(user_id,chat_id,'model',result)
                return {'text':result}
            if response.get('content'):contents.append(response['content'])
            parts=[]
            for call in calls:
                calls_used+=1
                if calls_used>self.settings.max_tool_calls:break
                try:
                    if knowledge_turn and call['name'] in WRITES:
                        raise PermissionError('RAG_READ_ONLY_TURN: gửi yêu cầu ghi riêng để xác nhận; tài liệu không cấp quyền điều khiển')
                    async with asyncio.timeout(self.settings.tool_timeout_seconds):
                        value=await self.tools.execute(call['name'],call['args'],user_id,chat_id,project_id)
                except (ValueError,PermissionError,TimeoutError) as error:
                    value={'state':'NOT_VERIFIED','error':sanitize(str(error))[:200]}
                if call['name']=='search_knowledge':
                    knowledge_citations=list(dict.fromkeys(knowledge_citations+knowledge_references(value)))[:3]
                if call['name']=='get_task_progress' and value.get('task_id') and value.get('acceptance_status'):live=value
                if value.get('state')=='CONFIRMATION_REQUIRED':
                    snapshot=value.get('snapshot') or {}
                    preview={key:value.get(key) for key in ('tool','arguments','project_id','scope_notice')}
                    preview['current_state']={key:snapshot.get(key) for key in ('task_id','version','latest_run_id','current_stage','current_agent','resume','acceptance_status','control')}
                    return {'text':'Đề nghị thao tác cần xác nhận riêng. '+json.dumps(preview,ensure_ascii=False),
                            'confirmation_id':value['confirmation_id']}
                verified.append(call['name'])
                parts.append({'function_response':{'name':call['name'],**({'id':call['id']} if call.get('id') else {}),
                    'response':{'result':context_result(value)}}})
            if parts:contents.append({'role':'user','parts':parts})
            if calls_used>=self.settings.max_tool_calls:break
        result='Đã chạm giới hạn xử lý. Đã truy vấn: '+', '.join(verified)+'. Phần còn lại chưa được xác minh; không có lệnh được tự xác nhận.'
        self.repo.append_message(user_id,chat_id,'model',result)
        return {'text':result}
