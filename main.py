import xmlrpc.client
from dotenv import load_dotenv
import os
import threading
import time
import sys

load_dotenv()
WORKERS = int(os.environ.get("WORKERS", 10))
DEFAULT_PORT = int(os.environ.get("DEFAULT_PORT", "8000"))

workers = []

for i in range(WORKERS):
    try:
        worker = {
            "name": "worker{}".format(i + 1),
            "status": 0,
            "proxy": xmlrpc.client.ServerProxy(
                "http://localhost:" + str(DEFAULT_PORT + i)
            ),
        }
        workers.append(worker)
    except Exception as e:
        print(e)


class Node:
    def __init__(self, name):
        self.name = name
        self.linked_pages = []
        self.all_searched = False

    def __str__(self):
        return self.name

    def getName(self):
        return self.name

    def addLink(self, page):
        self.linked_pages.append(page)

    def getLinkedPages(self):
        return self.linked_pages

    def getLinks(self):
        return [x.getName() for x in self.linked_pages]

    def resetLinkedPages(self):
        self.linked_pages = []

    def setAllSearched(self):
        self.all_searched = True

    def getAllSearched(self):
        return self.all_searched


search_depth = 1

# Traverse tree horizontally and find first empty child pages
def findNextPage(node, depth=1):
    global search_depth

    if node.getAllSearched() == False:
        for child in node.getLinkedPages():
            if child.getName() not in searched_pages:
                return child
            elif node.getLinkedPages().index(child) == len(node.getLinkedPages()) - 1:
                node.setAllSearched()

    if depth < search_depth:
        for child in node.getLinkedPages():
            next_node = findNextPage(child, depth + 1)
            if next_node != None:
                return next_node


# Update search depth based on last child's depth
def updateSearchDepth(root):
    global search_depth

    def getLastChild(node):
        if len(node.getLinkedPages()) == 0:
            return None
        else:
            return node.getLinkedPages()[-1]

    depth = 0
    last_child = root
    while True:
        last_child = getLastChild(last_child)
        if last_child == None:
            search_depth = depth
            break
        depth += 1


# At the end find the path from start to end
def findPath(root, end):
    path = [end]

    def findLink(node, link):
        if link in node.getLinks():
            return node.getName()
        for child in node.getLinkedPages():
            if link in child.getLinks():
                return child.getName()
        for child in node.getLinkedPages():
            next_link = findLink(child, link)
            if next_link != None:
                return next_link

    link = end
    while True:
        link = findLink(root, link)
        path.insert(0, link)
        if link == root.getName():
            break
    return path


# Find a worker that is not busy
def findWorker():
    stop_loop = False
    while not stop_loop:
        stop_loop = True
        for worker in workers:
            if worker["status"] == 0:
                return worker
            elif worker["status"] != -1:
                stop_loop = False


# Remove pages that are not real Wikipedia pages
def filterLinks(links):
    filtered_links = []
    for link in links:
        if not any(
            [
                x in link
                for x in [
                    "File:",
                    "Help:",
                    "Template:",
                    "Talk:",
                    "Template talk:",
                    "Wikipedia:",
                    "Category:",
                    "Module:",
                ]
            ]
        ):
            filtered_links.append(link)
    return filtered_links


# Get all links from a page using selected worker
def getLinks(worker, page):
    global page_found
    try:
        worker["status"] = 1
        links = worker["proxy"].getLinks(page.getName())
        if links == False:
            worker["status"] = 0
            searched_pages.remove(page.getName())
            return

        # Add links to parent page
        for link in filterLinks(links):
            if link not in searched_pages:
                page.addLink(Node(link))

        if end in links:
            page_found = True
        worker["status"] = 0

    # Handle worker errors
    except Exception as e:
        worker["status"] = -1
        searched_pages.remove(page.getName())
        page.resetLinkedPages()
        print(
            "Error: {}: {}".format(worker["name"], e),
            end=" " * 80 + "\n",
        )


# Use wroker to find out if a Wikipedia page exists
def checkIfPageExists(page_name):
    try:
        worker = findWorker()
        worker["status"] = 1
        links = worker["proxy"].getLinks(page_name)
        if links != False and len(links) > 0:
            return True
        else:
            return False
    except Exception as e:
        print(e)
    finally:
        worker["status"] = 0


# Loop through all pages and create worker threads
def mainLoop(start, end):
    root = Node(start)
    getLinks(workers[0], root)
    while True:
        try:
            if page_found:
                return findPath(root, end)

            # Find next page to search
            updateSearchDepth(root)
            page = findNextPage(root)
            if page == None:
                continue
            searched_pages.append(page.getName())

            # Find worker and start thread
            worker = findWorker()
            if worker == None:
                return None
            threading.Thread(
                target=getLinks,
                args=(
                    worker,
                    page,
                ),
            ).start()

        except KeyboardInterrupt:
            print(" " * 100, end="\r")
            print("Manual interrupt")
            return None
        except Exception as e:
            print(
                "Error: {}".format(e),
                end=" " * 80 + "\n",
            )


# Display status bar animation and page counter
def showLoading(start, end):
    bar = [
        "[=     ]",
        "[==    ]",
        "[ ==   ]",
        "[  ==  ]",
        "[   == ]",
        "[    ==]",
        "[     =]",
        "[    ==]",
        "[   == ]",
        "[  ==  ]",
        "[ ==   ]",
        "[==    ]",
    ]
    i = 0
    while show_loading:
        print(
            "Searching path from {} to {}... {} {} pages searched. Depth: {}".format(
                start, end, bar[i % len(bar)], len(searched_pages), search_depth
            ),
            end="\r",
        )
        time.sleep(0.075)
        i += 1


def main():
    global show_loading
    print("Starting the program...", end="\r")

    if start == end:
        print("Start and end page cannot be the same")
        return
    if not checkIfPageExists(end):
        print("End page does not exist")
        return
    if not checkIfPageExists(start):
        print("Start page does not exist")
        return

    threading.Thread(
        target=showLoading,
        args=(
            start,
            end,
        ),
    ).start()

    start_time = time.time()
    path = mainLoop(start, end)
    end_time = time.time()

    show_loading = False
    time.sleep(0.075)
    print(" " * 100, end="\r")

    if path == None:
        print("Failed to find path!")
        return

    print("Path found!")
    print("   " + path[0])
    for link in path[1:]:
        print("-> {}".format(link))
    print("Length: {} links.".format(len(path) - 1), end="")
    print(" {} pages searched.".format(len(searched_pages)))
    minutes, seconds = divmod(end_time - start_time, 60)
    print("Time taken: {:.0f} min {:.0f} s".format(minutes, seconds))


start = sys.argv[1]  # Start page
end = sys.argv[2]  # End page
searched_pages = []  # Pages that have already been searched
page_found = False  # Is the end page found in searched pages
show_loading = True  # Show loading animation

main()
