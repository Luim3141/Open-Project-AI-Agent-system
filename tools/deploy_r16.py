import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'openproject' / 'ai'))

from automation.engineering_deploy_continuation import deploy

if __name__ == '__main__':
    deploy('r16')
