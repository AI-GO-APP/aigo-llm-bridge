from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('windows_publisher',Path(__file__).resolve().parents[3]/'tools/publish_windows_installer.py')
publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)


def test_later_mandatory_policy_reuses_exact_published_binary():
    now=datetime.now(timezone.utc)
    old={'feed_sha256':'a'*64,'package_sha256':'b'*64,'commit':'c'*40,
         'minimum_version':'0.7.0','expires_at':(now+timedelta(days=20)).isoformat()}
    assert publisher.same_release_action(old,dict(old),now)=='unchanged'
    assert publisher.same_release_action(old,{**old,'minimum_version':'0.7.1'},now)=='refresh'
    with pytest.raises(ValueError):publisher.same_release_action(old,{**old,'package_sha256':'d'*64},now)
    with pytest.raises(ValueError):publisher.same_release_action(old,{**old,'minimum_version':'0.6.9'},now)
    due={**old,'expires_at':(now+timedelta(days=6)).isoformat()}
    assert publisher.same_release_action(due,dict(due),now)=='refresh'
