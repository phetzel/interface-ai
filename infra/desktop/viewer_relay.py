"""Forward viewer bytes to one fixed service; never accept a destination from clients.

Docker Desktop does not publish the internal-only desktop network's port on this
host. This separate relay joins both networks; the desktop retains no default
route. The relay has no host mounts, credentials, or generic proxy capability.
"""

import selectors
import socket
import socketserver


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            with socket.create_connection(('desktop', 6080), timeout=5) as upstream:
                upstream.settimeout(10)
                self.request.settimeout(10)
                with selectors.DefaultSelector() as selector:
                    selector.register(self.request, selectors.EVENT_READ, upstream)
                    selector.register(upstream, selectors.EVENT_READ, self.request)
                    while True:
                        for key, _ in selector.select(timeout=30):
                            data = key.fileobj.recv(65536)
                            if not data:
                                return
                            key.data.sendall(data)
        except (OSError, TimeoutError):
            return


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == '__main__':
    with Server(('0.0.0.0', 6080), Handler) as server:
        print('Viewer relay: fixed upstream desktop:6080', flush=True)
        server.serve_forever()
