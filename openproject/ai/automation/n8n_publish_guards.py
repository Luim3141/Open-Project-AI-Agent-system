"""Fail closed when a publish does not match its tested Gateway or n8n is busy."""


def verify_runtime(expected,current):
    if not expected or current!=expected:
        raise ValueError('GATEWAY_RUNTIME_NOT_QUALIFIED')


def verify_idle(state):
    if type(state.get('unfinished')) is not int or state['unfinished']!=0:
        raise ValueError('N8N_NOT_IDLE')
