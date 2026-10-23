"""Bounded, disposable schema validation. Caller data stays in stdin and RAM."""
import json
import sys
import threading

from .errors import BridgeError

MAX_SCHEMA_BYTES=262144
MAX_NODES=8192
MAX_DEPTH=24
MAX_PAYLOAD=8_000_000
VALIDATION_SECONDS=3
CAPACITY=threading.BoundedSemaphore(4)


def bounds(schemas,parameter):
    try:
        if len(json.dumps(schemas).encode())>MAX_SCHEMA_BYTES:raise ValueError()
        stack=[(s,0) for s in schemas];nodes=0
        while stack:
            value,depth=stack.pop();nodes+=1
            if nodes>MAX_NODES or depth>MAX_DEPTH:raise ValueError()
            if isinstance(value,dict):
                # Recursive/local refs can expand without a finite work budget.
                if {'$ref','$dynamicRef'}&value.keys():raise ValueError()
                stack.extend((v,depth+1) for v in value.values())
            elif isinstance(value,list):stack.extend((v,depth+1) for v in value)
    except (ValueError,RecursionError):
        raise BridgeError(400,'unsupported_parameter','Schema 超過安全複雜度限制，或包含目前不支援的引用。',parameter) from None


def run(payload,cancel=None):
    from .process import Child
    if getattr(sys,'frozen',False):
        from pathlib import Path
        parent=Path(sys.executable).parent
        candidates=[parent/'aigo-bridge.exe',parent/'BYO-Setup/AIGO-Bridge-Setup.exe',parent/'AIGO-Bridge-Setup.exe']
        cli=next((p for p in candidates if p.is_file()),Path(sys.executable))
        command=[str(cli),'--schema-validate']
    else:command=[sys.executable,'-m','desktop_bridge.schema_guard']
    raw=json.dumps(payload,separators=(',',':')).encode()
    if len(raw)>MAX_PAYLOAD:return 'limit'
    if not CAPACITY.acquire(blocking=False):return 'busy'
    # Isolated cwd is unnecessary: no file/tool/remote reference is accepted.
    from pathlib import Path
    from .providers import environment
    env=environment();env['PYINSTALLER_RESET_ENVIRONMENT']='1'
    child=None
    try:
        child=Child(command,str(Path(__file__).resolve().parent.parent),env,memory_limit=256*1024*1024)
        answer=json.loads(child.communicate(raw,cancel or threading.Event(),VALIDATION_SECONDS))
        return answer.get('status','invalid')
    except BridgeError as error:
        if error.category=='cancelled':raise
        return 'limit'
    except (OSError,ValueError):return 'limit'
    finally:
        if child:child.close()
        CAPACITY.release()


def check_schemas(schemas,parameter):
    bounds(schemas,parameter)
    result=run({'schemas':schemas})
    if result=='busy':raise BridgeError(429,'queue_full','Schema 驗證已達並行上限，請稍後再試。')
    if result!='ok':
        raise BridgeError(400,'unsupported_parameter' if result=='limit' else 'invalid_request',
            'Schema 無效或超過安全驗證預算。',parameter)


def validate_instances(pairs,cancel=None):
    # Schemas already passed check_schemas before inference.
    return run({'pairs':pairs},cancel)=='ok'


def main():
    from jsonschema import Draft202012Validator,SchemaError,ValidationError
    status='invalid'
    try:
        raw=sys.stdin.buffer.read(MAX_PAYLOAD+1)
        if len(raw)>MAX_PAYLOAD:raise ValueError()
        value=json.loads(raw)
        if set(value)=={'schemas'}:
            for schema in value['schemas']:Draft202012Validator.check_schema(schema)
        elif set(value)=={'pairs'}:
            for schema,instance in value['pairs']:Draft202012Validator(schema).validate(instance)
        else:raise ValueError()
        status='ok'
    except (ValueError,TypeError,KeyError,SchemaError,ValidationError,RecursionError):pass
    # No exception text, schema, value or traceback may enter stdout/stderr.
    sys.stdout.write(json.dumps({'status':status}))


if __name__=='__main__':main()
