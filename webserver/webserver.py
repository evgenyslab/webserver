import argparse
import os
import pkg_resources as p
import http.server
from bs4 import BeautifulSoup
import urllib.request
import socket
import socketserver
import warnings

"""
Web Server python tool servers a directy
by reading the index.html in the pack's web folder,
parses the scripts, and inserts the scripts into a 
single HTML file and servers the HTML to clients.

A custom directory can be provided and the process
repeats

HOW TO PASS PARAMETERS TO WEBPAGE?

-> pass kwargs,
-> when parsing scripts, find matching 
parameters and replace with kwards
"""


def checkExtension(file, extensions=()):
    if len(extensions) == 0:
        return True
    else:
        return file.endswith(extensions)


def fileFinder(directory=[], extensions=(), walk=True):

    if isinstance(directory, str):
        directory = [directory]

    files = []
    paths = []
    for k in directory:
        if os.path.isfile(k) and checkExtension(k, extensions):
            files.append(k)
        elif os.path.isdir(k):
            paths.append(k)

    for k in paths:
        if walk:
            for dirpath, dirnames, filenames in os.walk(k):
                for filename in filenames:
                    if checkExtension(filename, extensions):
                        files.append((dirpath, filename))
        else:
            for f in os.listdir(k):
                if os.path.isfile(k + "/" + f) and checkExtension((k + "/" + f), extensions):
                    files.append((k + "/", f))

    return files


def generateHandler(html):
    """
    Generates an http.server.BaseHTTPRequestHandler that is triggered on webrequest

    :param html: path to root html file
    :return:
    """

    class MyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            """Respond to a GET request."""
            if self.path == '/':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode())

            else:
                self.send_error(404)

    return MyHandler


class Webserver:
    """

    """
    def __init__(self, **kwargs):
        """!

        @param host:
        @param port:
        """

        # DEFAULTS
        self.host = "0.0.0.0"
        self.sources = ""
        self.port = 0
        self.html = ""
        self.server = None

        self.sourceDirectory = ""
        self.sourceIndexFile = ""

        if 'sources' not in kwargs:
            raise(ValueError, "Input not provided")
        if not (os.path.isfile(kwargs['sources']) or os.path.isdir(kwargs['sources'])):
            raise(ValueError, "Error: input is neither a file or a directory")

        if 'port' in kwargs:
            self.port = kwargs['port']

        if 'host' in kwargs:
            # validate:
            try:
                socket.inet_aton(kwargs['host'])
            except socket.error:
                warnings.warn("Request Host at {:} is not available, reverting to default {:}".format(kwargs['host'],
                                                                                                      self.host))

        # parse sources:
        # Single FILE:
        if os.path.isfile(kwargs['sources']):
            # validate is it html file:
            if not kwargs['sources'].endswith('html'):
                raise(ValueError, "input file {:} is not html".format(kwargs['sources']))
            else:
                self.sourceIndexFile = kwargs['sources']
                self.sourceDirectory = '/'.join(self.sourceIndexFile.split('/')[:-1]) + '/'

        # SERVE FOLDER
        else:  # folder
            self.sourceDirectory = kwargs['sources'] + '/' if kwargs['sources'][-1] != '/' else ''
            self.sourceFiles = fileFinder(self.sourceDirectory)
            # find index file:
            fileList = [k[-1] for k in self.sourceFiles]
            if fileList.count('index.html') == 0:
                raise(ValueError, "No index.html file found in directory provided.")
            elif fileList.count('index.html') > 1:
                raise (ValueError, "More than one index.html file found in directory provided.")
            else:
                idx = fileList.index('index.html')
                self.sourceIndexFile = ''.join(self.sourceFiles[idx])
                # remove the file from source list:
                self.sourceFiles.pop(idx)

        self.parseIndexHTMLFile()
        self.handler = generateHandler(self.html)



    def parseIndexHTMLFile(self):
        """
        Read the sourceIndexFile
        -> determine if it calls for scripts that need to be inserted & are available locally
        -> determine if it calls for remote scripts (check if they can curl)
        """
        with open(self.sourceIndexFile, "r") as f:
            doc = f.read()
        soup = BeautifulSoup(doc, 'html.parser')
        fileList = [k[-1] for k in self.sourceFiles]
        scripts = soup.find_all('script')
        # check each script...
        for script in scripts:
            # try this if HTTP
            if script['src'].startswith('http'):
                try:
                    # TODO: just check if page is available;
                    page = urllib.request.urlopen(script['src'])
                    scriptRaw = page.read()
                except:
                    # couldn't fetch page
                    pass
            else:
                # local file
                if script['src'] in fileList:
                    idx = fileList.index(script['src'])
                    with open(''.join(self.sourceFiles[idx]), "r") as f:
                        scriptRaw = f.read()
                else:
                    pass
                script.string = scriptRaw  # raw js UTF-8
                del(script['src'])  # remove tag

        # now, convert the soup back to byte-doc
        self.html = str(soup)  # and serve it :)

    def serve(self):
        """

        :return:
        """
        print("Starting web serving at: http://{:s}:{:d}\n\n".format(self.host,self.port))
        # TODO: Handle error if port is not free!
        self.server = socketserver.TCPServer(("", self.port), self.handler, bind_and_activate=False)
        self.server.allow_reuse_address = True
        try:
            self.server.server_bind()
            self.server.server_activate()
        except:
            self.server.server_close()
            raise

        # Star the server
        self.server.serve_forever()


if __name__ == "__main__":
    # input args needs to be an index.html file or directory
    parser = argparse.ArgumentParser(description='Simple Web Server')

    parser.add_argument("-i",
                        dest="sources",
                        required=True,
                        help="Web Source Location")

    parser.add_argument("--host",
                        dest="hostAddress",
                        default="0.0.0.0")

    parser.add_argument("--port",
                        dest="port",
                        default="12345",
                        type=int)

    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()

    # args.default should be an index.html
    server = Webserver(sources=args.sources,
                       host=args.hostAddress,
                       port=args.port)
    server.serve()
