"""Provider output shape only; Native graph/role/version validation belongs to native_wbs."""
import copy
import re
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from .presentation import safe_text


class Requirement(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    id:str=Field(min_length=1,max_length=40)
    text:str=Field(min_length=1,max_length=1000)


class Node(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    key:str=Field(min_length=1,max_length=24)
    kind:Literal['Epic','Task','Subtask']
    subject:str=Field(min_length=1,max_length=240)
    requirement_ids:list[str]=Field(min_length=1,max_length=80)
    parent:str|None=None
    depends_on:list[str]=Field(default_factory=list,max_length=50)
    description:str=Field(default='',max_length=4000)
    status_id:int|None=Field(default=None,gt=0)
    duplicate_disposition:str|None=Field(default=None,max_length=1000)
    assignee_role:Literal['PM','BA','BA-PM','BE','FE','QA']|None=None
    priority_id:int|None=Field(default=None,gt=0)
    start_date:str|None=None
    due_date:str|None=None


class Planning(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    format_name:Literal['QLDAPM_WBS_V1']=Field(alias='schema')
    requirements:list[Requirement]=Field(min_length=1,max_length=80)
    nodes:list[Node]=Field(min_length=1,max_length=50)


class Relation(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    predecessor:str=Field(min_length=1,max_length=24)
    successor:str=Field(min_length=1,max_length=24)
    lag:int=Field(ge=-2000,le=2000)


class PlanningV2(Planning):
    format_name:Literal['QLDAPM_WBS_V2']=Field(alias='schema')
    relations:list[Relation]=Field(max_length=100)


def safe_plan(value):
    if isinstance(value,dict):return {k:safe_plan(v) for k,v in value.items()}
    if isinstance(value,list):return [safe_plan(v) for v in value]
    return safe_text(value) if isinstance(value,str) else value


def native_keys(payload):
    nodes=payload.get('nodes')
    if not isinstance(nodes,list) or not 1<=len(nodes)<=50:raise ValueError('WBS_BA_NODE_KEYS_REQUIRED')
    keys=[node.get('key') if isinstance(node,dict) else None for node in nodes]
    if any(not isinstance(key,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,23}',key) for key in keys):raise ValueError('WBS_BA_NODE_KEY_INVALID')
    mapping={key:key.lower() for key in keys}
    if len(set(mapping.values()))!=len(keys):raise ValueError('WBS_BA_NODE_KEY_COLLISION')
    if all(key==value for key,value in mapping.items()):return payload,{}
    result=copy.deepcopy(payload)
    def reference(key):
        if not isinstance(key,str) or key not in mapping:raise ValueError('WBS_BA_NODE_REFERENCE_INVALID')
        return mapping[key]
    for node in result['nodes']:
        node['key']=reference(node['key'])
        if node.get('parent') is not None:node['parent']=reference(node['parent'])
        if 'depends_on' in node:
            if not isinstance(node['depends_on'],list):raise ValueError('WBS_BA_NODE_REFERENCE_INVALID')
            node['depends_on']=[reference(key) for key in node['depends_on']]
    relations=result.get('relations',[])
    if not isinstance(relations,list):raise ValueError('WBS_BA_NODE_REFERENCE_INVALID')
    for edge in relations:
        if not isinstance(edge,dict):raise ValueError('WBS_BA_NODE_REFERENCE_INVALID')
        for field in ['predecessor','successor']:edge[field]=reference(edge.get(field))
    return result,mapping


def provider_schema(value):
    # Gemini's grammar compiler rejects large nested bounds; Pydantic still enforces every bound on return.
    if isinstance(value,list):return [provider_schema(v) for v in value]
    if not isinstance(value,dict):return value
    result={k:provider_schema(v) for k,v in value.items() if k not in {
        'title','default','maxItems','minItems','maxLength','minLength','minimum','maximum','exclusiveMinimum','exclusiveMaximum'}}
    if result.get('type')=='object' and 'properties' in result:
        result['required']=list(result['properties'])
    return result
