import os
import sys
from pathlib import Path

# Make the project root importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bincom_project.settings')

from bincom_project.wsgi import application as app  # noqa: E402
