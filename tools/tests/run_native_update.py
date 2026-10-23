"""CI-only diagnostics wrapper; no arbitrary CLI output enters public logs."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('native_update_probe',ROOT/'tools/verify_installer_update.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
original=probe.run


def diagnostic(*args,**kwargs):
    try:return original(*args,**kwargs)
    except subprocess.CalledProcessError as error:
        tree=ast.parse((ROOT/'desktop_bridge/windows_updates.py').read_text())
        known=[node.args[0].value for node in ast.walk(tree) if isinstance(node,ast.Call)
            and isinstance(node.func,ast.Name) and node.func.id=='UpdateError' and node.args
            and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str)]
        known.append('Operation failed; check the selected profile and installer guide.')
        raw=error.stderr or ''
        if isinstance(raw,bytes):raw=raw.decode('utf-8','replace')
        category=next((message for message in known if message in raw),'Unknown native CLI failure')
        print(json.dumps({'native_cli_failed':True,'return_code':error.returncode,'safe_error':category}),flush=True)
        raise


if __name__=='__main__':
    probe.run=diagnostic
    probe.main()
