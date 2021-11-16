#!/bin/python
import csv
import hashlib
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
accounts_db = {"john": "23423"}
channels = {} # key: channel name, value: list of clients

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
        ready_to_read, ready_to_write, in_error = select.select(sockets_list, [], [], 0)

        for notified_socket in ready_to_read:
            # If a connection request is received
            if notified_socket == server_socket:
                client_socket, client_address = server_socket.accept()
                sockets_list.append(client_socket)
                clients[client_socket] = client_address
                print(f"Accepted new connection from client {client_address[0]}:{client_address[1]}")

            # If a message is received from a client, not a new connection
            else:
                try:
                    received_msg = receive_message(notified_socket)

                    if received_msg is False:
                        print(f"Closed connection from {clients[notified_socket][0]}:{clients[notified_socket][1]}")
                        sockets_list.remove(notified_socket)
                        del clients[notified_socket]
                        broadcast(server_socket, notified_socket, f"Client {client_address[0]}:{client_address[1]} is offline".encode("utf-8"))
                        continue

                    received_msg = received_msg['data'].decode("utf-8")
                    client_address = clients[notified_socket]
                    print(f"Received message from client {client_address[0]}:{client_address[1]} > {received_msg}")

                    if received_msg.split(' ')[0].startswith("LOGIN"):
                        username = received_msg.split(' ')[1]
                        password = received_msg.split(' ')[2]
                        password = hashlib.sha256(str.encode(password)).hexdigest()
                        # If user doesn't exist
                        if username not in accounts_db:
                            # Send RESULT message back to client
                            result_msg = "RESULT LOGIN 0".encode("utf-8")
                            result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                            notified_socket.send(result_header + result_msg)
                            continue
                        # If user exists
                        else:
                            if accounts_db[username] == password:
                                clients[notified_socket] = username
                                result_msg = "RESULT LOGIN 1".encode("utf-8")
                                result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                                notified_socket.send(result_header + result_msg)
                                print(f"Client {username} logged in")
                            else:
                                result_msg = "RESULT LOGIN 0".encode("utf-8")
                                result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                                notified_socket.send(result_header + result_msg)
                                print(f"Client {username} failed to log in")

                    elif received_msg.split(' ')[0].startswith("REGISTER"):
                        username = received_msg.split(' ')[1]
                        password = received_msg.split(' ')[2]
                        password = hashlib.sha256(str.encode(password)).hexdigest()
                        accounts_db[username] = password
                        result_msg = "RESULT REGISTER 1".encode("utf-8")
                        result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                        notified_socket.send(result_header + result_msg)
                        print(f"New client {username} registered")

                    elif received_msg.split(' ')[0].startswith("JOIN"):
                        channel = received_msg.split(' ')[1]

                        # If channel doesn't exist
                        if channel not in channels:
                            result_msg = f"RESULT JOIN {channel} 0".encode("utf-8")
                            result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                            notified_socket.send(result_header + result_msg)
                            print(f"Channel {channel} does not exist.")
                        # If channel exists
                        else:
                            # Let client join the channel
                            channels[channel].append(clients[notified_socket])
                            result_msg = f"RESULT JOIN {channel} 1".encode("utf-8")
                            result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                            notified_socket.send(result_header + result_msg)
                            print(f"Client joined channel {channel}.")

                    elif received_msg.split(' ')[0].startswith("CREATE"):
                        channel = received_msg.split(' ')[1]

                        # If channel already exists
                        if channel in channels:
                            result_msg = f"RESULT CREATE {channel} 0".encode("utf-8")
                            result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                            notified_socket.send(result_header + result_msg)
                            print(f"Channel {channel} already exists.")
                        else:
                            channels[channel] = []
                            result_msg = f"RESULT JOIN {channel} 1".encode("utf-8")
                            result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                            notified_socket.send(result_header + result_msg)
                            print(f"Created channel {channel}.")

                    elif received_msg.split(' ')[0].startswith("SAY"):
                        channel = received_msg.split(' ')[1]
                        message = received_msg.split(' ')[2]
                        print(channel)
                        print(message)

                        # If user is not in the channel
                        if clients[notified_socket] not in channels[channel]:
                            result_msg = f"You have not joined {channel}".encode("utf-8")
                            result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                            notified_socket.send(result_header + result_msg)
                            print(f"Client failed to join channel {channel}.")
                        else:
                            result_msg = f"RECV {client_address[0]}:{client_address[1]} {channel} {message}".encode("utf-8")
                            result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                            notified_socket.send(result_header + result_msg)
                            # broadcast(server_socket, notified_socket, message.encode("utf-8"))
                    elif received_msg == "CHANNELS":
                        result_msg = str(channels.values).encode("utf-8")
                        result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                        notified_socket.send(result_header + result_msg)
                    else:
                        result_msg = "INVALID REQUEST".encode("utf-8")
                        result_header = f"{len(result_msg):<{HEADER_LENGTH}}".encode("utf-8")
                        notified_socket.send(result_header + result_msg)

                    # broadcast(server_socket, notified_socket,
                    #           user['header'] + user['data'] + received_msg['header'] + received_msg['data'])

                except Exception as e:
                    broadcast(server_socket, notified_socket, f"Client {client_address[0]}:{client_address[1]} is offline".encode("utf-8"))
                    continue


def broadcast(server_sock, sock, message):
    for s in sockets_list:
        if s != server_sock and s != sock:
            try:
                message_header = f"{len(message):<{HEADER_LENGTH}}".encode("utf-8")
                s.send(message_header + message)
            except:
                s.close()
                if s in sockets_list:
                    sockets_list.remove(s)


if __name__ == '__main__':
    run()
