"""Mac 可獨立建置,不需要 Windows 工具鏈。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_desktop import build
if __name__ == '__main__':
    build('macos', Path(__file__).resolve().parents[2] / 'dist' / 'macos')
