"""Source-checkout entry point for installer-owned Cloudflare setup."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from desktop_bridge.byo import main
if __name__=='__main__':raise SystemExit(main())
