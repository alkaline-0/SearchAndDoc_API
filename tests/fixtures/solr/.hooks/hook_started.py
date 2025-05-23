import os
from time import monotonic

import requests
from dotenv import load_dotenv

load_dotenv()

start = monotonic()
connected = False
timeout = 5
conn_url = f"http://{os.getenv('SOLR_HOST_TEST')}:{os.getenv('SOLR_PORT_TEST')}/solr"
while not connected:
    try:
        response = requests.get(conn_url)
        connected = True
    except Exception:
        if monotonic() - start > timeout:
            raise TimeoutError()
