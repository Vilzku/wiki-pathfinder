from dotenv import load_dotenv
import os
from subprocess import Popen

try:
    load_dotenv()
    WORKERS = int(os.environ.get("WORKERS", 50))
    DEFAULT_PORT = int(os.environ.get("DEFAULT_PORT", "8000")) + 1

    for i in range(WORKERS):
        port = DEFAULT_PORT + i
        Popen("python worker.py worker{} {}".format(i + 1, str(port)))

except Exception as e:
    print(e)
    input("Press enter to exit...")
