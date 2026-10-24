from pathlib import Path
import subprocess
import sys

import pytest

from tools.benchmark_api_latency import valid


@pytest.mark.parametrize('probability,expected',[(.5,True),(True,False),(float('nan'),False),(-.1,False)])
def test_latency_validates_decision_type_range_and_finiteness(probability,expected):
    body={'model':'synthetic','answers':{'q':{'type':'noul','noul':probability}}}
    assert valid(body,'synthetic','decisions') is expected
    assert not valid(body,'different-model','decisions')


def test_latency_opt_in_required_before_profile_access(tmp_path):
    root=Path(__file__).resolve().parents[2]
    output=tmp_path/'result.json'
    result=subprocess.run([sys.executable,str(root/'tools/benchmark_api_latency.py'),
        '--install-root',str(tmp_path/'missing'),'--label','test','--output',str(output)],
        capture_output=True,timeout=5)
    assert result.returncode==2 and not output.exists() and b'Traceback' not in result.stderr
