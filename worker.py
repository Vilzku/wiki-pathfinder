from xmlrpc.server import SimpleXMLRPCServer
import sys
import requests

NAME = sys.argv[1]
PORT = int(sys.argv[2])
worker = SimpleXMLRPCServer(("localhost", PORT), logRequests=False)
print(NAME + " started in port " + str(PORT))

WIKI_URL = "https://en.wikipedia.org/w/api.php"


def getLinks(page):
    print(NAME + " received request for: " + page)
    params = {"action": "parse", "page": page, "format": "json", "prop": "links"}
    response = requests.get(url=WIKI_URL, params=params)
    data = response.json()
    if data.get("error") is not None:
        return []
    page_data = data.get("parse")
    if page_data is None:
        return False
    links = page_data.get("links")
    if links is None:
        return False
    return [link["*"] for link in links]


worker.register_function(getLinks, "getLinks")
worker.serve_forever()
