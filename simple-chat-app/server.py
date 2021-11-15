#!/bin/python
import csv
import select
import signal
import os
import sys
import socket


# Use this variable for your loop
daemon_quit = False

HEADER_LENGTH = 10
IP = "127.0.0.1"

"""
AF_INET: address domain of the socket
SOCK_STREAM: type of socket, SOCK_STREAM means that data or characters are read in a continuous flow.
"""
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sockets_list = []
clients = {}
accounts_db = {"john": 23423}


# Do not modify or remove this handler
def quit_gracefully(signum, frame):
    global daemon_quit
    daemon_quit = True


def create_account():
    pass


def confirm_login(username, password):
    pass


def setup_socket(port):
    try:
        server_socket.bind((IP, port))
    except socket.error as e:
        print(str(e))

    print("Waiting for a connection...")
    server_socket.listen()

    sockets_list.append(server_socket)


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False

        message_length = int(message_header.decode("utf-8").strip())
        return {"header": message_header, "data": client_socket.recv(message_length)}

    except:
        return False


def run():
    # Do not modify or remove this function call
    signal.signal(signal.SIGINT, quit_gracefully)

    if len(sys.argv) != 3:
        print("Wrong usage. Use script [port number] [configuration]")
        exit()

    setup_socket(int(sys.argv[1]))

    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

        for notified_socket in read_sockets:
            if notified_socket == server_socket:
                client_socket, client_address = server_socket.accept()

                user = receive_message(client_socket)
                if user is False:
                    continue
                # TODO: Check LOGIN message format

                print(user['data'].decode("utf-8"))
                # Check if user exists
                if user['data'].decode("utf-8") not in accounts_db:
                    # Send RESULT message back to client
                    result_msg = "RESULT LOGIN :0".encode("utf-8")
                    result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                    client_socket.send(result_header + result_msg)
                else:
                    sockets_list.append(client_socket)

                    clients[client_socket] = user

                    print(f"Accepted new connection from {client_address[0]}:{client_address[1]} username: {user['data'].decode('utf-8')}")

            else:
                message = receive_message(notified_socket)

                if message is False:
                    print(f"Closed connection from {clients[notified_socket]['data'].decode('utf-8')}")
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    continue

                user = clients[notified_socket]
                print(f"Received message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')}")

                for client_socket in clients:
                    if client_socket != notified_socket:
                        client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

        for notified_socket in exception_sockets:
            sockets_list.remove(notified_socket)
            del clients[notified_socket]


if __name__ == '__main__':
    run()


