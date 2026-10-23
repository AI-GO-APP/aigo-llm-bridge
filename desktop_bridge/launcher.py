import sys
from pathlib import Path

if not getattr(sys,"frozen",False): sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from desktop_bridge.__main__ import main

if __name__=="__main__":
    if sys.argv[1:]==['--schema-validate']:
        from desktop_bridge.schema_guard import main as validate
        validate()
    else:raise SystemExit(main())
