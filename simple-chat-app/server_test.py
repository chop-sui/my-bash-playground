import unittest
import server
import client

import hashlib
import select
import signal
import sys
import socket

# Server setting
HEADER_LENGTH = 2048
IP = "127.0.0.1"
PORT = 1234
sockets_list = []
clients = {}  # key: client_socket, value: client_address
online_clients_username = {}  # key: client_address, value: client username
accounts_db = {}
channels = {}  # key: channel name, value: list of clients

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


class ServerTest(unittest.TestCase):
    def test_connect_to_server(self):

        server.setup_socket(PORT)
        self.assertEqual(len(server.sockets_list), 1)


if __name__ == '__main__':
    unittest.main()
