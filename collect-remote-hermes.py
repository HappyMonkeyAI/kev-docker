"""Read-only SSH-side collection of bounded, private review candidates; emits JSONL."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3


def redact(text):
    text = re.sub(r'(?i)\bBearer\s+[^\s"\x27]+', 'Bearer [REDACTED]', text)
    text = re.sub(r'\b(?:sk-|hf_)[A-Za-z0-9_-]{12,}\b', '[REDACTED_TOKEN]', text)
    text = re.sub(r'(?i)(\b(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*)[^\s,;]+', r'\1[REDACTED]', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[REDACTED_EMAIL]', text)
    return text


def main():
    conn = sqlite3.connect('file:'+str(Path.home()/'.hermes/state.db')+'?mode=ro', uri=True)
    sessions = conn.execute('select id,parent_session_id from sessions where source=? order by started_at desc limit 215', ('cli',)).fetchall()
    parent = dict(sessions)
    def group(session_id):
        seen = set()
        while parent.get(session_id) and session_id not in seen:
            seen.add(session_id)
            session_id = parent[session_id]
        return hashlib.sha256(('215:'+session_id).encode()).hexdigest()[:16]
    mapping = {'read_file':'inspect','search_files':'inspect','web_search':'research',
               'web_extract':'research','write_file':'execute','patch':'execute','clarify':'clarify'}
    rows = []
    for session_id, _ in sessions:
        prior_assistant = ''
        current = None
        for message_id, role, content, calls in conn.execute(
                'select id,role,content,tool_calls from messages where session_id=? and active=1 and compacted=0 order by timestamp,id', (session_id,)):
            if role == 'user':
                current = None
                if isinstance(content,str) and 20 <= len(content.strip()) <= 8000 and not content.lstrip().startswith(('[Your active task list', '[CONTEXT COMPACTION', '[Continuing toward your standing goal]', '[Context summary', '[Session summary')):
                    session_group = group(session_id)
                    current = {'id':f'hermes-215-{session_group}-{message_id}',
                               'session_group':session_group, 'split':'test' if int(session_group[:8],16)%4==0 else 'dev',
                               'state':{'user_request':redact(content)},
                               'preceding_assistant_excerpt':redact(prior_assistant[:4000]),
                               'context_excerpt_truncated':len(prior_assistant)>4000,
                               'observed_tools':[], 'observed_route_hint':None,
                               'review_status':'pending','expected_route':None,
                               'context_complete':False,'privacy_reviewed':False,
                               'review_note':'CLI history is not proof of human authorship. Verify intent/context and labels; observed calls are hints only.'}
                    rows.append(current)
            elif role == 'assistant':
                if current is not None and calls:
                    try:
                        parsed = json.loads(calls)
                        names = [call.get('function',{}).get('name',call.get('name')) for call in parsed if isinstance(call,dict)]
                        names = [name for name in names if isinstance(name,str)]
                    except (ValueError,TypeError,AttributeError):
                        names = []
                    if names:
                        current['observed_tools'] = names
                        routes = {mapping.get(name) for name in names}
                        current['observed_route_hint'] = routes.pop() if len(routes)==1 else None
                        current = None
                if isinstance(content,str) and content.strip():
                    prior_assistant = content
    conn.close()
    # Identical requests are kept once; no observed labels are approved.
    seen = set()
    unique = []
    for row in rows:
        text = row['state']['user_request'].strip()
        if text not in seen:
            seen.add(text)
            unique.append(row)
    # Limit collected personal content, preserving some less common route hints.
    selected = []
    for hint in ('clarify','research','execute','inspect',None):
        selected.extend([row for row in unique if row['observed_route_hint']==hint][:30])
    for row in selected:
        print(json.dumps(row,ensure_ascii=False))


if __name__ == '__main__':
    main()
