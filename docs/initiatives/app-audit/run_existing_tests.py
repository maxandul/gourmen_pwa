"""Run existing tests with in-memory DB, no dotenv and no outbound sockets.

Uses the bundled Python with the existing project site-packages because the
local venv launcher points to a Python installation unavailable in this session.
No dependency installation and no changes to application/test code.
"""
from pathlib import Path
import os
import socket
import sys

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / 'venv/Lib/site-packages'))
sys.path.insert(0, str(ROOT))
for key in list(os.environ):
    if key.upper() not in {'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'COMSPEC', 'PATHEXT'}:
        del os.environ[key]
os.environ.update(FLASK_ENV='testing', DATABASE_URL='sqlite:///:memory:',
                  PYTHON_DOTENV_DISABLED='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
import dotenv
dotenv.load_dotenv = lambda *args, **kwargs: False


def no_network(*args, **kwargs):
    raise RuntimeError('Audit test runner blocks outbound network access')


socket.socket.connect = no_network
socket.create_connection = no_network
if __name__ == '__main__':
    import pytest
    raise SystemExit(pytest.main(['tests', '-q', '-p', 'no:cacheprovider']))
