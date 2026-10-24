import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from desktop_bridge.store import Store
from tools import mac_service


@pytest.mark.parametrize('workers,pending',[(0,64),(65,64),(True,64),(32,31),(32,65),(32,False)])
def test_invalid_mac_capacity_never_pauses_or_stops(tmp_path,monkeypatch,workers,pending):
    app=Path(__file__).resolve().parents[2]
    monkeypatch.setattr(mac_service.sys,'platform','darwin')
    monkeypatch.setattr(mac_service,'manifest_at',lambda *_:{'app':str(app),'data_dir':str(tmp_path/'data')})
    calls=[];monkeypatch.setattr(mac_service,'setup',lambda *args:calls.append(args))
    with pytest.raises(ValueError):mac_service.control('workers',tmp_path,workers=workers,pending=pending)
    assert not calls
    store=Store(tmp_path/'data',startup=False)
    try:assert store.get('inference_workers')==64 and store.get('inference_pending')==64
    finally:store.close()


@pytest.mark.skipif(os.name=='nt',reason='macOS helper uses a POSIX profile lock; no Windows native claim.')
def test_mac_capacity_pair_preserves_accepting_profile_and_restart_order(tmp_path,monkeypatch):
    app=Path(__file__).resolve().parents[2];data=tmp_path/'data'
    store=Store(data);device_id=store.get('device_id');store.set('accepting',False);store.close()
    m={'app':str(app),'data_dir':str(data)}
    monkeypatch.setattr(mac_service.sys,'platform','darwin')
    monkeypatch.setattr(mac_service,'manifest_at',lambda *_:m)
    calls=[]
    monkeypatch.setattr(mac_service,'setup',lambda m,action,*_:calls.append(action) or '{}')
    monkeypatch.setattr('desktop_bridge.windows.mac_startup_path',lambda *_:tmp_path/'agent.plist')
    monkeypatch.setattr('desktop_bridge.windows.set_startup',lambda *_:None)
    monkeypatch.setattr(mac_service.subprocess,'run',lambda args,**_:SimpleNamespace(returncode=1 if 'print' in args else 0))
    mac_service.control('workers',tmp_path,workers=32,pending=64)
    store=Store(data,startup=False)
    try:
        assert (store.get('inference_workers'),store.get('inference_pending'))==(32,64)
        assert store.get('device_id')==device_id and store.get('accepting') is False
    finally:store.close()
    assert calls==['pause','wait-idle','pause','status']
