import argparse
import os
import random
import http.server
import socketserver
import warnings
from threading import Thread


class Webserver:
    """
    A class for serving a directory or an html string
    
    Input options:
        dir
        fileList
        html string
    """
    def __init__(self, **kwargs):
        """!

        @param host:
        @param port:
        """
        self.__sample_html__ = '''
                                <meta http-equiv="refresh" content="30" />
                                <html>
                                <head>
                                <title>(Type a title for your page here)</title>
                                <script type="text/javascript"> 
                                function display_c(){
                                var refresh=1000; // Refresh rate in milli seconds
                                mytime=setTimeout('display_ct()',refresh)
                                }
                                
                                function display_ct() {
                                var x = new Date()
                                document.getElementById('ct').innerHTML = x;
                                display_c();
                                 }
                                </script>
                                </head>
                                
                                <body onload=display_ct();>
                                <span id='ct' ></span>
                                
                                </body>
                                </html>
                                '''
        # DEFAULTS
        self.host = "0.0.0.0"
        self.port = 7777
        self.html = None
        self.directory = None
        self.file_list = None
        self.__serving_html__ = None
        self.__parse_inputs__(**kwargs)
        self.__decide_what_to_serve__()
        self.server = None
        self.is_serving = False
        self.__serving_thread__ = None
        # TODO: resolve inputs

    @staticmethod
    def __generate_handle__(html=""):
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

    def __parse_inputs__(self, **kwargs):
        self.host = kwargs.get('host', self.host)
        self.port = kwargs.get('port', self.port)
        self.html = kwargs.get('html', self.html)
        self.directory = kwargs.get('directory', self.directory)
        self.file_list = kwargs.get('file_list', self.file_list)

    def __decide_what_to_serve__(self):
        """
        Decides on what inputs to serve by priority:
            Directory
            File List
            HTML
        """
        # check if self.dir or self.fileList, default to self.html if none of the previous
        # successfully parsed
        if self.html is not None:
            self.__serving_html__ = self.html
        else:
            self.__serving_html__ = self.__sample_html__

    def __serve_with_thread__(self, host, port, html):
        # TODO: auto inject refresh line '<meta http-equiv="refresh" content="30" />'
        bound = False
        handler = self.__generate_handle__(html)
        while not bound:
            self.server = socketserver.TCPServer(("", port), handler, bind_and_activate=False)
            self.server.allow_reuse_address = True
            try:
                self.server.server_bind()
                self.server.server_activate()
                bound = True
            except OSError:
                # could not bind; maybe, choose a random port then
                warnings.warn("Port {:} in use".format(port))
                self.server.server_close()
                port = random.randrange(9999, 13000)

        # Star the server
        print("Starting web serving at: http://{:s}:{:d}\n\n".format(host, port))
        self.server.serve_forever()

    def start(self):
        """

        :return:
        """
        if self.is_serving:
            return
        if self.__serving_html__ is None:
            return
        self.__serving_thread__ = Thread(target=self.__serve_with_thread__, args=(self.host, self.port, self.__serving_html__, ))
        self.__serving_thread__.start()
        self.is_serving = True

    def __del__(self):
        self.stop()

    def stop(self):
        if not self.is_serving:
            return

        def stop_server():
            self.server.shutdown()

        __thread__ = Thread(target=stop_server)
        __thread__.start()
        __thread__.join()
        self.__serving_thread__.join()
        self.is_serving = False
        print("stopped")

    def serve(self, **kwargs):
        """
        Generic server/re-serve
        html
        port
        host
        """
        self.stop()
        self.__parse_inputs__(**kwargs)
        self.__decide_what_to_serve__()
        self.start()

#
# if __name__ == "__main__":
#     # input args needs to be an index.html file or directory
#     parser = argparse.ArgumentParser(description='Simple Web Server')
#
#     parser.add_argument("-i",
#                         dest="sources",
#                         required=True,
#                         help="Web Source Location")
#
#     parser.add_argument("--host",
#                         dest="hostAddress",
#                         default="0.0.0.0")
#
#     parser.add_argument("--port",
#                         dest="port",
#                         default="12345",
#                         type=int)
#
#     parser.add_argument('--version', action='version', version='%(prog)s 1.0')
#
#     args = parser.parse_args()
#
#     # args.default should be an index.html
#     server = Webserver(sources=args.sources,
#                        host=args.hostAddress,
#                        port=args.port)
#     server.serve()
