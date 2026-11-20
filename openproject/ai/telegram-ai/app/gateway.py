import asyncio
import json

import httpx

from .config import secret


class GatewayError(ValueError): pass


class GatewayClient:
    def __init__(self,settings):
        self.settings=settings
        self.last_correlation_id=None
        self.client=httpx.AsyncClient(base_url=settings.gateway_url,timeout=settings.tool_timeout_seconds,
                                      follow_redirects=False,trust_env=False)

    async def close(self): await self.client.aclose()

    async def command(self,action,args,project_id,idempotency_key=None):
        if project_id not in self.settings.project_ids:raise PermissionError('PROJECT_NOT_ALLOWED')
        bearer=secret(self.settings.service_credential,self.settings.service_credential_file)
        if not bearer:raise GatewayError('GATEWAY_CREDENTIAL_MISSING')
        body={'action':action,'arguments':args,'project_id':project_id}
        if idempotency_key:body['idempotency_key']=idempotency_key
        try:
            response=await self.client.post('/api/v1/commands',json=body,headers={'Authorization':'Bearer '+bearer},
                timeout=60 if action=='observer_active' and not args.get('summary_only') else self.settings.tool_timeout_seconds)
        except httpx.HTTPError:
            # A timeout is never a reason to retry a business write with a new key.
            raise GatewayError('GATEWAY_UNREACHABLE_OR_OUTCOME_UNKNOWN') from None
        if response.status_code>=400:
            try:code=response.json().get('code') or response.json().get('error','')
            except ValueError:code=''
            safe=str(code).split(':',1)[0].split(' ',1)[0][:100]
            raise GatewayError(f'GATEWAY_HTTP_{response.status_code} {safe}')
        try:data=response.json()
        except ValueError:raise GatewayError('GATEWAY_INVALID_RESPONSE') from None
        if 'result' not in data:raise GatewayError('GATEWAY_INVALID_RESPONSE')
        self.last_correlation_id=data.get('correlation_id')
        return data['result']

    async def proposal_decision(self,proposal_id,proposal_hash):
        # Only a previously stored exact Gateway proposal may reach this fixed endpoint.
        import uuid
        uuid.UUID(proposal_id)
        if len(proposal_hash)!=64 or any(c not in '0123456789abcdef' for c in proposal_hash):
            raise ValueError('INVALID_PROPOSAL_HASH')
        bearer=secret(self.settings.service_credential,self.settings.service_credential_file)
        try:response=await self.client.post(f'/api/v1/proposals/{proposal_id}/decision',
            json={'decision':'approve','hash':proposal_hash},headers={'Authorization':'Bearer '+bearer})
        except httpx.HTTPError:raise GatewayError('GATEWAY_OUTCOME_UNKNOWN_RECONCILE_FIRST') from None
        if response.status_code>=400:raise GatewayError('GATEWAY_PROPOSAL_REJECTED_'+str(response.status_code))
        return response.json()
