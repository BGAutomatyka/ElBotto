from __future__ import annotations
import os, yaml
from dataclasses import dataclass
from pathlib import Path

CRED_DIR = Path(os.path.expanduser('~/.elbo'))
CRED_PATH = CRED_DIR/'credentials.yaml'

@dataclass
class ApiKeys:
    api_key: str = ''
    api_secret: str = ''
    testnet: bool = False

    @classmethod
    def load(cls) -> 'ApiKeys':
        try:
            if CRED_PATH.exists():
                data = yaml.safe_load(open(CRED_PATH,'r')) or {}
                return cls(api_key=str(data.get('api_key','') or ''), api_secret=str(data.get('api_secret','') or ''), testnet=bool(data.get('testnet', False)))
        except Exception:
            pass
        return cls()

    def save(self):
        CRED_DIR.mkdir(parents=True, exist_ok=True)
        with open(CRED_PATH,'w') as f:
            yaml.safe_dump({'api_key': self.api_key, 'api_secret': self.api_secret, 'testnet': bool(self.testnet)}, f, sort_keys=False)
        try:
            os.chmod(CRED_PATH, 0o600)
        except Exception:
            pass
