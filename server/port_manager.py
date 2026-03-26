import socket

START_PORT = 8001
END_PORT = 8100

def find_free_port() -> int:
    for port in range(START_PORT, END_PORT):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(("localhost", port))
            if result != 0:
                return port
    raise RuntimeError("No free ports available in range 8001-8100")