"""Research ingestion candidate: whole bounded journals, explicit current Native fields."""
import hashlib,json

def document_text(wp,activities,sanitize,*,max_chars=64000):
    if wp.get('_links',{}).get('project',{}).get('href')!='/api/v3/projects/6':raise PermissionError('PROJECT6_SOURCE_REQUIRED')
    title=sanitize(wp['subject']);description=sanitize(wp.get('description',{}).get('raw',''))
    fields={'native_id':wp['id'],'lock_version':wp['lockVersion'],
            'status':wp['_links']['status']['title'],'type':wp['_links']['type']['title']}
    header=json.dumps({'native_fields':fields},ensure_ascii=False,sort_keys=True)
    text=title+'\n'+header+'\n'+description
    if len(text)>max_chars:raise ValueError('SOURCE_DESCRIPTION_TOO_LARGE_NO_TRUNCATION')
    remaining=max_chars-len(text);selected=[];omitted=[]
    comments=sorted((a for a in activities if type(a.get('id')) is int and a['id']>0 and (a.get('comment') or {}).get('raw')),key=lambda a:a['id'])
    for activity in reversed(comments[-20:]):
        raw=sanitize(activity['comment']['raw']);piece='\nBình luận #'+str(activity['id'])+': '+raw
        if len(piece)>remaining:omitted.append(activity['id']);continue
        selected.append((activity['id'],piece,hashlib.sha256(raw.encode()).hexdigest()));remaining-=len(piece)
    selected.sort();text+=''.join(row[1] for row in selected)
    return text,{'native_fields':fields,'native_header':{'start':len(title)+1,'end':len(title)+1+len(header),'sha256':hashlib.sha256(header.encode()).hexdigest()},
                 'activity_ids':[row[0] for row in selected],
                 'activity_hashes':{str(row[0]):row[2] for row in selected},'omitted_activity_ids':sorted(omitted),
                 'history_before_latest20_omitted':max(0,len(comments)-20),'partial_json_truncation':False}
