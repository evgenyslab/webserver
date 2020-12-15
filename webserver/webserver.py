import http.server
import socketserver
import threading
import os
import pkg_resources as p

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


def generate_handler(html):
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
                for script in scripts:
                    self.wfile.write("\n\n<script>".encode())
                    self.wfile.write(script.encode())
                    self.wfile.write("\n\n</script>".encode())

            else:
                self.send_error(404)

    return MyHandler


class webserver:
    """

    """
    def __init__(self, **kwargs):
        """!

        @param host:
        @param port:
        """

        #TODO: host in kwargs
        #TODO: serveDirectory in kwargs
        #TODO: self-contained async loop instead of thread maybe

        # DEFAULTS
        self.host = "0.0.0.0"

        html, script = self.__getSources__(serveDirectory=serveDirectory)
        self.__loadWebFiles__(html=html, script=script, commport=commport)
        self.handler = generate_handler(self.html, scripts=[self.script])
        self.host = host
        self.port = port
        self.server = None
        self.serving = False
        self.serverThread = None
        self.start()

    def parseArgs(self, **kwargs):
       pass 

    def __loadWebFiles__(self, html="", script="", commport=0):
        assert(html != "")
        assert(script != "")
        assert(commport != 0)
        with open(html, "r") as f:
            self.html = f.read()
        with open(script, "r") as f:
            self.script = f.read()
        # set requested communication port
        self.script = self.script.replace("port: \"7777\"", "port: \"" + str(commport) + "\"")
        # add local plotly & msgpack scripts:
        scriptPlotly = p.resource_filename('webplot', 'web/plotly-latest.min.js')
        scriptMsgpack = p.resource_filename('webplot', 'web/msgpack.min.js')
        assert (os.path.isfile(scriptPlotly))
        assert (os.path.isfile(scriptMsgpack))
        with open(scriptPlotly, "r") as f:
            scriptPlotlyRaw = f.read()
        with open(scriptMsgpack, "r") as f:
            scriptMsgpackRaw = f.read()

        self.html = self.html + "\n\n" + \
                                "<script>" + scriptMsgpackRaw + "</script>\n" + \
                                "<script>" + scriptPlotlyRaw + "</script>\n"



    @staticmethod
    def __getSources__(serveDirectory=""):
        if serveDirectory != "":
            htmlExternal = serveDirectory + ('/' if serveDirectory[-1] != '/' else '') + 'index.html'
            scriptExternal = serveDirectory + ('/' if serveDirectory[-1] != '/' else '') + 'visualizer.js'
            # check if it is a directory
            if os.path.isdir(serveDirectory) and  os.path.isfile(htmlExternal) and  os.path.isfile(scriptExternal):
                return htmlExternal, scriptExternal
        else:
            html = p.resource_filename('webplot', 'web/index.html')
            script = p.resource_filename('webplot', 'web/visualizer.js')
            assert(os.path.isfile(html))
            assert(os.path.isfile(script))
            return html, script

    def stop(self):
        """

        :return:
        """
        self.server.shutdown()
        self.serverThread.join()
        print("Stopping web serving")

    def start(self):
        """

        :return:
        """
        self.serverThread = threading.Thread(target=self.serve)
        self.serverThread.start()
        self.serving = True

    def serve(self):
        """

        :return:
        """
        print("Starting web serving at: http://{:s}:{:d}\n\n".format(self.host,self.port))
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

