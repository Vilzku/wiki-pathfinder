from dotenv import load_dotenv
import os
from subprocess import Popen

try:
    load_dotenv()
    WORKERS_LIST = os.environ.get("WORKERS", "worker").split(" ")
    DEFAULT_PORT = int(os.environ.get("DEFAULT_PORT", "8000"))
    if WORKERS_LIST == None:
        raise "WORKERS environment variable not set"

    for worker in WORKERS_LIST:
        port = str(DEFAULT_PORT + WORKERS_LIST.index(worker))
        Popen("python worker.py {} {}".format(worker, str(port)))

except Exception as e:
    print(e)
    input("Press enter to exit...")
