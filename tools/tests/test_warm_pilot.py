"""The live experiment must opt in and validate capacity before touching CLI/profile."""
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('args', [[], ['--apply','--resident','2','--concurrency','1'],
    ['--apply','--resident','-1'], ['--apply','--concurrency','65']])
def test_pilot_rejects_missing_opt_in_or_invalid_budget_before_install_read(tmp_path,args):
    output=tmp_path/'report.json'
    result=subprocess.run([sys.executable,str(ROOT/'tools/benchmark_warm_cli.py'),*args,
        '--install-root',str(tmp_path/'does-not-exist'),'--output',str(output)],capture_output=True,timeout=5)
    assert result.returncode==2 and not output.exists()
    assert b'Traceback' not in result.stderr
