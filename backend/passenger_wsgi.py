import sys, os
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path: sys.path.insert(0, APP_DIR)
os.environ.setdefault("FLASK_ENV", "production")
from run import app as application
