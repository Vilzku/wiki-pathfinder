from dotenv import load_dotenv
import xmlrpc.client
import os
import threading
import time
import sys

load_dotenv()
WORKERS = int(os.environ.get("WORKERS", 50))
DEFAULT_PORT = int(os.environ.get("DEFAULT_PORT", "8000")) + 1


class Worker:
    def __init__(self, name, port):
        self.name = name
        self.proxy = xmlrpc.client.ServerProxy("http://localhost:" + str(port))
        self.status = 0  # 0: idle, 1: busy, -1: dead

    def getName(self):
        return self.name

    def getStatus(self):
        return self.status

    def setStatus(self, status):
        self.status = status

    def getLinks(self, page):
        return self.proxy.getLinks(page)


def initWorkers():
    workers = []
    for i in range(WORKERS):
        workers.append(Worker("worker" + str(i + 1), DEFAULT_PORT + i))
    return workers


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


# Traverse tree horizontally and find first empty child pages
def findNextPage(node, depth=1):
    if node.getAllSearched() == False:
        for child in node.getLinkedPages():
            if child.getName() not in searched_pages:
                searched_pages.append(child.getName())
                return child
            elif child.getName() == node.getLinkedPages()[-1].getName():
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
        if node.getLinkedPages() == []:
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
    loop = True
    while loop:
        loop = False
        for worker in workers:
            if worker.getStatus() == 0:
                worker.setStatus(1)
                return worker
            elif worker.getStatus() != -1:
                # Keep looping if any worker is still alive
                loop = True


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
def getLinks(worker, root, end):
    global page_found
    try:
        if root.getLinkedPages() == []:
            page = root
        else:
            page = findNextPage(root)
        while page == None and not page_found:
            time.sleep(0.5)
            page = findNextPage(root)

        links = worker.getLinks(page.getName())
        if links == False:
            worker.setStatus(0)
            searched_pages.remove(page.getName())
            return

        for link in filterLinks(links):
            if link not in searched_pages:
                page.addLink(Node(link))

        if end in links:
            page_found = True
        worker.setStatus(0)

    # Handle worker errors
    except Exception as e:
        if not page_found:
            worker.setStatus(-1)
            searched_pages.remove(page.getName())
            page.resetLinkedPages()
            print(" " * 100, end="\r")
            print("Error: {}: {}".format(worker.getName(), e))


# Use wroker to find out if a Wikipedia page exists
def checkIfPageExists(page_name):
    try:
        worker = findWorker()
        links = worker.getLinks(page_name)
        if links != False and len(links) > 0:
            return True
        else:
            return False
    except Exception as e:
        print(e)
    finally:
        worker.setStatus(0)


# Keep going until end page is found
def mainLoop(start, end):
    root = Node(start)
    getLinks(workers[0], root, end)
    while True:
        try:
            if page_found:
                return findPath(root, end)
            updateSearchDepth(root)
            worker = findWorker()
            if worker == None:
                return None
            threading.Thread(
                target=getLinks,
                args=(
                    worker,
                    root,
                    end,
                ),
            ).start()
        except KeyboardInterrupt:
            print(" " * 100, end="\r")
            print("Manual interrupt")
            return None
        except Exception as e:
            print(" " * 100, end="\r")
            print("Error: {}".format(e))


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
    while finding_path:
        print(
            "Searching path from {} to {}... {} {} pages searched. Depth: {}".format(
                start, end, bar[i % len(bar)], len(searched_pages), search_depth
            ),
            end="\r",
        )
        time.sleep(0.075)
        i += 1


def main():
    global finding_path
    print("Starting the program...", end="\r")

    start = sys.argv[1]
    end = sys.argv[2]

    if start[0].islower() or end[0].islower():
        print(
            "Cannot run: Make sure you have typed the page names correctly (capital letters)"
        )
        return
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
    minutes, seconds = divmod(end_time - start_time, 60)

    finding_path = False
    time.sleep(0.075)
    print(" " * 100, end="\r")

    if path == None:
        print("Failed to find path!")
    else:
        print("Path found!")
        print("   " + path[0])
        for link in path[1:]:
            print("-> {}".format(link))
        print("Length: {} links.".format(len(path) - 1), end="")
        print(" {} pages searched.".format(len(searched_pages)))
        print("Time taken: {:.0f} min {:.0f} s".format(minutes, seconds))


if len(sys.argv) < 3:
    print("Usage: python main.py <start page> <end page>")
    exit()

searched_pages = []  # Pages that have already been searched
search_depth = 1  # How deep in the links the search currently is, root=0
page_found = False  # Is the end page found in searched pages
finding_path = True  # Show animation during path finding
workers = initWorkers()  # Workers used to fetch links from Wikipedia API

main()
