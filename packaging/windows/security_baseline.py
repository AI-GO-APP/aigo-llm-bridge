"""Windows release runtime baseline, including components pip does not scan."""
import re
import ssl
import sys
from importlib.metadata import version


def inventory():
    import certifi
    import hashlib
    from pathlib import Path
    return {'python':'.'.join(map(str,sys.version_info[:3])),
            'openssl':ssl.OPENSSL_VERSION,'certifi':version('certifi'),
            'ca_sha256':hashlib.sha256(Path(certifi.where()).read_bytes()).hexdigest()}


def check():
    value=inventory()
    openssl=tuple(map(int,re.search(r'(\d+)\.(\d+)\.(\d+)',value['openssl']).groups()))
    certifi=tuple(map(int,value['certifi'].split('.')))
    if sys.version_info[:3]<(3,14,9) or openssl<(3,5,9) or certifi<(2026,10,19):
        raise ValueError('Windows security runtime baseline not met.')
    return value
