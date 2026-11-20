import os
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


def secret(value, file):
    if value.strip():return value.strip()
    if file:
        try: return Path(file).read_text(encoding='utf-8').strip()
        except (FileNotFoundError, PermissionError): return ''
    return value.strip()


class Settings(BaseModel):
    model_config = ConfigDict(extra='forbid')
    db_path: Path = Path('/state/telegram.sqlite')
    bot_token: str = Field(default='', repr=False)
    gemini_api_key: str = Field(default='', repr=False)
    gemini_model: str = 'gemini-3.5-flash-lite'
    gateway_url: str = 'http://gateway:8090'
    service_credential_file: str = ''
    service_credential: str = Field(default='', repr=False)
    internal_secret_file: str = ''
    n8n_webhook_url: str = ''
    notification_webhook_secret_file: str = ''
    notification_poll_seconds: int = Field(default=30, ge=5, le=300)
    project_ids: list[int] = Field(default_factory=list)
    polling_enabled: bool = True
    notifications_enabled: bool = True
    allow_webhook_removal: bool = False
    max_tool_rounds: int = Field(default=5, ge=1, le=8)
    max_tool_calls: int = Field(default=12, ge=1, le=20)
    request_timeout_seconds: int = Field(default=90, ge=10, le=180)
    tool_timeout_seconds: int = Field(default=20, ge=1, le=60)
    max_output_tokens: int = Field(default=1500, ge=100, le=4096)
    max_daily_model_calls: int = Field(default=20, ge=1, le=1000)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=60)
    provider_data_consent: bool = False

    @field_validator('gateway_url')
    @classmethod
    def internal_gateway(cls, value):
        parsed=urlparse(value)
        if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('INVALID_GATEWAY_URL')
        return value.rstrip('/')

    @field_validator('project_ids')
    @classmethod
    def projects(cls, value):
        if not value or all(type(v) is int and v>0 for v in value): return sorted(set(value))
        raise ValueError('POSITIVE_PROJECT_IDS_REQUIRED')

    @classmethod
    def from_env(cls):
        env=os.environ
        def boolean(key,default): return env.get(key,str(default)).lower() in {'1','true','yes'}
        return cls(db_path=env.get('TELEGRAM_AI_DB_PATH','/state/telegram.sqlite'),
            bot_token=secret(env.get('TELEGRAM_BOT_TOKEN',''),env.get('TELEGRAM_BOT_TOKEN_FILE','')),
            gemini_api_key=secret(env.get('GEMINI_API_KEY',''),env.get('GEMINI_API_KEY_FILE','')),
            gemini_model=env.get('GEMINI_MODEL','gemini-3.5-flash-lite'),
            gateway_url=env.get('QLDAPM_GATEWAY_INTERNAL_URL','http://gateway:8090'),
            service_credential_file=env.get('QLDAPM_SERVICE_CREDENTIAL_REF',''),
            service_credential=env.get('QLDAPM_SERVICE_CREDENTIAL',''),
            internal_secret_file=env.get('TELEGRAM_AI_INTERNAL_SECRET_FILE',''),
            n8n_webhook_url=env.get('TELEGRAM_AI_N8N_WEBHOOK_URL',''),
            notification_webhook_secret_file=env.get('TELEGRAM_AI_N8N_WEBHOOK_SECRET_FILE',''),
            notification_poll_seconds=int(env.get('TELEGRAM_AI_NOTIFICATION_POLL_SECONDS','30')),
            project_ids=[int(v.strip()) for v in env.get('QLDAPM_ALLOWED_PROJECT_IDS','').split(',') if v.strip()],
            polling_enabled=boolean('TELEGRAM_POLLING_ENABLED',True),
            notifications_enabled=boolean('TELEGRAM_NOTIFICATIONS_ENABLED',True),
            allow_webhook_removal=boolean('TELEGRAM_ALLOW_WEBHOOK_REMOVAL',False),
            max_tool_rounds=int(env.get('TELEGRAM_AI_MAX_TOOL_ROUNDS','5')),
            max_tool_calls=int(env.get('TELEGRAM_AI_MAX_TOOL_CALLS','12')),
            request_timeout_seconds=int(env.get('TELEGRAM_AI_REQUEST_TIMEOUT_SECONDS','90')),
            max_daily_model_calls=int(env.get('TELEGRAM_AI_MAX_DAILY_MODEL_CALLS','20')),
            provider_data_consent=boolean('GEMINI_PROJECT_DATA_CONSENT',False))

    def missing(self):
        return [name for name,present in [('TELEGRAM_BOT_TOKEN',bool(self.bot_token)),
            ('QLDAPM_SERVICE_CREDENTIAL_REF',bool(secret(self.service_credential,self.service_credential_file))),
            ('QLDAPM_ALLOWED_PROJECT_IDS',bool(self.project_ids))] if not present]
