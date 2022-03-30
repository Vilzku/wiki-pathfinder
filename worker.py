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
    try:
        response = requests.get(url=WIKI_URL, params=params)
        data = response.json()
        links = data["parse"]["links"]
        return [link["*"] for link in links]
    except Exception as e:
        print("Error: " + str(e))
        return None


worker.register_function(getLinks, "getLinks")
worker.serve_forever()
