import os
import sys
import threading
import time
import webbrowser

# Ensure root directory in python path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import create_app
from backend.database.db import init_db

def open_browser():
    """Waits 1 second for the server to bind, then automatically opens the browser window."""
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == '__main__':
    # Initialize database tables
    init_db()
    
    app = create_app()
    print("\n" + "=" * 65)
    print("  🛡️  CashTrace AI (SIH-26184) IS LIVE AND RUNNING!")
    print("  🌐  Opening browser window automatically at: http://127.0.0.1:8000")
    print("=" * 65 + "\n")
    
    # Launch browser automatically in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host='127.0.0.1', port=8000, debug=False)