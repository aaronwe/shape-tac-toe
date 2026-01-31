from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys

class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

if __name__ == '__main__':
    port = 8000
    print(f"Serving on port {port} with no-cache headers...")
    httpd = HTTPServer(('localhost', port), NoCacheHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
