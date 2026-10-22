"""Shared profile locations. Provider logins never select a bridge profile."""
import os
from pathlib import Path
import sys


def default_directory():
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/AIGO LLM Bridge/data'
    return Path(os.environ.get('LOCALAPPDATA') or Path.home()) / 'AIGO LLM Bridge/data'
