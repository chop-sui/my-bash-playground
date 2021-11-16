import socket
import select
import errno
import sys
import msvcrt

HEADER_LENGTH = 2048
IP = "127.0.0.1"
PORT = 1234


def chat_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))

    print("Connected to server!")
    sys.stdout.write("Enter command: ")
    sys.stdout.flush()

    while True:
        # For Windows OS, select() does not accept objects other than socket
        # socket_list = [sys.stdin, client_socket]
        # ready_to_read, ready_to_write, in_error = select.select(socket_list, [], [])
        # So, we can change the above line as follows
        ready_to_read, ready_to_write, in_error = select.select((client_socket,), (), (), 1)
        if msvcrt.kbhit():
            ready_to_read.append(sys.stdin)

        for sock in ready_to_read:
            if sock == client_socket:
                # Incoming message from server
                result_header = client_socket.recv(HEADER_LENGTH)
                if not len(result_header):
                    print("Connection closed by the server")
                    sys.exit()
                else:
                    # result_length = int(result_header.decode("utf-8").strip())
                    result = result_header.decode("utf-8")

                    sys.stdout.write(f"{result}\n")
                    sys.stdout.write("Enter command: ")
                    sys.stdout.flush()

            else:
                # user enters a message
                msg = sys.stdin.readline()

                if msg.startswith("LOGIN") or msg.startswith("REGISTER") or msg.startswith("JOIN") or msg.startswith(
                        "CREATE") or msg.startswith("SAY") or msg.startswith("CHANNELS"):
                    data = msg.encode("utf-8")
                    data_header = f"{len(data):<{HEADER_LENGTH}}".encode("utf-8")
                    client_socket.send(data)

                else:
                    msg = msg.encode("utf-8")
                    msg_header = f"{len(msg):<{HEADER_LENGTH}}".encode("utf-8")
                    client_socket.send(msg)
                #sys.stdout.write("Enter command: ")
                sys.stdout.flush()


if __name__ == "__main__":
    chat_client()

# while True:
#     message = input(f"{my_username} > ")
#
#     if message:
#         message = message.encode("utf-8")
#         message_header = f"{len(message):<{HEADER_LENGTH}}".encode("utf-8")
#         client_socket.send(message_header + message)
#
#     try:
#         # Keep attempting to receive any incoming messages
#         while True:
#             username_header = client_socket.recv(HEADER_LENGTH)
#             if not len(username_header):
#                 print("Connection closed by the server")
#                 sys.exit()
#
#             username_length = int(username_header.decode("utf-8").strip())
#             username = client_socket.recv(username_length).decode("utf-8")
#
#             message_header = client_socket.recv(HEADER_LENGTH)
#             message_length = int(message_header.decode("utf-8").strip())
#             message = client_socket.recv(message_length).decode("utf-8")
#
#             print(f"{username} > {message}")
#
#     except IOError as e:
#         if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
#             print('Reading error', str(e))
#         continue
#
#     except Exception as e:
#         print('General error', str(e))
#         sys.exit()
