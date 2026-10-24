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

PROBE_STAGES={'renderer_ready','onboarding_renderer','default_key','native_key_copy',
    'same_key_http','native_csv_export','browser_adapter','metadata_only_profile','complete',
    'native_key_click','native_key_read'}
PROBE_CHECKS={'actual_webview2_adapter_ready','product_branding_rendered',
    'onboarding_first_launch_or_daily_bypass','onboarding_five_steps_rendered','onboarding_consent_defaults_off',
    'frontend_new_key_all_checked','default_key_all_providers','actual_frontend_key_copy_exact',
    'copied_key_authenticates','native_csv_exact_metadata_columns','native_csv_contains_synthetic_row',
    'csv_does_not_contain_key','csv_save_selection_supplied_by_test','browser_frontend_remains_available',
    'key_not_stored_plaintext'}


def safe_probe(value):
    return {'success':value.get('success') is True,
        'stage':value.get('stage') if value.get('stage') in PROBE_STAGES else 'unknown',
        'checks':{k:v for k,v in value.get('checks',{}).items() if k in PROBE_CHECKS and type(v) is bool}}


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
        command=list(map(str,args[0]))
        if '--console-probe' in command and '--data-dir' in command:
            directory=Path(command[command.index('--data-dir')+1])
            for name in ('windows-console-probe.json','windows-console-progress.json'):
                try:
                    value=json.loads((directory/name).read_text())
                    print(json.dumps({'native_console_metadata':safe_probe(value)}),flush=True)
                except (OSError,ValueError,TypeError):pass
        raise


if __name__=='__main__':
    probe.run=diagnostic
    probe.main()
