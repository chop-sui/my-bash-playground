#!/bin/python
import hashlib
import select
import signal
import sys
import socket

# Use this variable for your loop
daemon_quit = False

HEADER_LENGTH = 2048
IP = "127.0.0.1"

"""
AF_INET: address domain of the socket
SOCK_STREAM: type of socket, SOCK_STREAM means that data or characters are read in a continuous flow.
"""
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sockets_list = []
clients = {}  # key: client_socket, value: client_address
online_clients_username = {}  # key: client_address, value: client username
accounts_db = {"john": "23423"}
channels = {}  # key: channel name, value: list of clients


# Do not modify or remove this handler
def quit_gracefully(signum, frame):
    global daemon_quit
    daemon_quit = True


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

        # message_length = int(message_header.decode("utf-8").strip())
        # print(message_header.decode("utf-8"))
        return {"header": message_header, "data": message_header.decode("utf-8")}

    except:
        return False


def run():
    # Do not modify or remove this function call
    signal.signal(signal.SIGINT, quit_gracefully)

    if len(sys.argv) > 3:
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
                # At this point, the user has not logged in nor registered. So, just let username be client_address
                online_clients_username[client_address] = client_address
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

                    received_msg = received_msg['data']
                    client_address = clients[notified_socket]
                    print(f"Received message from client {client_address[0]}:{client_address[1]} > {received_msg}")

                    if received_msg.split(' ')[0].startswith("LOGIN"):
                        username = received_msg.split(' ')[1]
                        password = received_msg.split(' ')[2]
                        password = hashlib.sha256(str.encode(password)).hexdigest()

                        # If user doesn't exist
                        if username not in accounts_db:
                            # Send RESULT message back to client
                            result_msg = "RESULT LOGIN 0\n".encode("utf-8")
                            notified_socket.send(result_msg)
                            continue

                        # If user exists
                        else:
                            if accounts_db[username] == password:
                                # If user is already logged in
                                if username in online_clients_username.values():
                                    result_msg = "RESULT LOGIN 0\n".encode("utf-8")
                                    notified_socket.send(result_msg)
                                    print(f"Client {username} is already logged in")
                                else:
                                    online_clients_username[client_address] = username
                                    result_msg = "RESULT LOGIN 1\n".encode("utf-8")
                                    notified_socket.send(result_msg)
                                    print(f"Client {username} logged in")
                            else:
                                result_msg = "RESULT LOGIN 0\n".encode("utf-8")
                                notified_socket.send(result_msg)
                                print(f"Client {username} failed to log in")

                    elif received_msg.split(' ')[0].startswith("REGISTER"):
                        username = received_msg.split(' ')[1]
                        password = received_msg.split(' ')[2]
                        password = hashlib.sha256(str.encode(password)).hexdigest()

                        # If username already exists
                        if username in accounts_db:
                            result_msg = "RESULT REGISTER 0\n".encode("utf-8")
                            notified_socket.send(result_msg)
                            print(f"Username {username} already exists. Failed to register")
                        else:
                            accounts_db[username] = password

                            result_msg = "RESULT REGISTER 1\n".encode("utf-8")
                            notified_socket.send(result_msg)
                            print(f"New client {username} registered")

                    elif received_msg.split(' ')[0].startswith("JOIN"):
                        channel = received_msg.split(' ')[1].strip()
                        username = online_clients_username[client_address]

                        # If channel doesn't exist
                        if channel not in channels:
                            result_msg = f"RESULT JOIN {channel} 0\n".encode("utf-8")
                            notified_socket.send(result_msg)
                            print(f"Channel {channel} does not exist.")

                        # If channel exists
                        else:
                            # If user is already in the channel
                            if clients[notified_socket] in channels[channel]:
                                result_msg = f"RESULT JOIN {channel} 0\n".encode("utf-8")
                                notified_socket.send(result_msg)
                                print(f"Client {username} is already in channel {channel}")
                            else:
                                # Let client join the channel
                                channels[channel].append(clients[notified_socket])
                                result_msg = f"RESULT JOIN {channel} 1\n".encode("utf-8")
                                notified_socket.send(result_msg)
                                print(f"Client {username} has joined channel {channel}.")

                    elif received_msg.split(' ')[0].startswith("CREATE"):
                        channel = received_msg.split(' ')[1].strip()
                        username = online_clients_username[client_address]

                        # If channel already exists
                        if channel in channels:
                            result_msg = f"RESULT CREATE {channel} 0\n".encode("utf-8")
                            notified_socket.send(result_msg)
                            print(f"Channel {channel} already exists.")
                        else:
                            channels[channel] = []
                            result_msg = f"RESULT CREATE {channel} 1\n".encode("utf-8")
                            notified_socket.send(result_msg)
                            print(f"Client {username} created channel {channel}.")

                    elif received_msg.split(' ')[0].startswith("SAY"):
                        channel = received_msg.split(' ')[1]
                        message = received_msg[find_nth(received_msg, ' ', 2) + 1:]
                        username = online_clients_username[client_address]

                        # If user is not in the channel
                        if clients[notified_socket] not in channels[channel]:
                            result_msg = f"You have not joined {channel} yet\n".encode("utf-8")
                            notified_socket.send(result_msg)
                            print(f"Client {username} failed to join channel {channel}.")
                        else:
                            result_msg = f"RECV {username} {channel} {message}".encode("utf-8")
                            notified_socket.send(result_msg)

                    elif received_msg[:received_msg.find(' ')] == "CHANNELS":
                        channels_str = ""
                        for key in sorted(channels.keys()):
                            channels_str += key + ", "
                        channels_str = channels_str.strip()
                        if channels_str.endswith(','):
                            channels_str = channels_str[:-1]
                        result_msg = f"RESULT CHANNELS {channels_str}\n".encode("utf-8")
                        notified_socket.send(result_msg)

                    # Handle any other type of messages sent from client
                    else:
                        result_msg = "INVALID REQUEST\n".encode("utf-8")
                        notified_socket.send(result_msg)

                except Exception as e:
                    broadcast(server_socket, notified_socket, f"Client {client_address[0]}:{client_address[1]} is offline".encode("utf-8"))
                    continue


def broadcast(server_sock, sock, message):
    for s in sockets_list:
        if s != server_sock and s != sock:
            try:
                # message_header = f"{len(message):<{HEADER_LENGTH}}".encode("utf-8")
                s.send(message)
            except:
                s.close()
                if s in sockets_list:
                    sockets_list.remove(s)


def find_nth(word, substring, n):
    start = word.find(substring)
    while start >= 0 and n > 1:
        start = word.find(substring, start+len(substring))
        n -= 1
    return start


if __name__ == '__main__':
    run()
