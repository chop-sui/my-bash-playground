import socket
import select
import sys
import msvcrt
import json

clientside_test_result = {
    "tc1_can_connect_to_server": False,
    "tc2_can_get_message_from_server": False,
    "tc3_can_send_message_to_server": False,
}
HEADER_LENGTH = 2048
IP = "127.0.0.1"
# PORT = 1234


def chat_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, int(sys.argv[1])))

    clientside_test_result["tc1_can_connect_to_server"] = True
    write_json()
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
                    write_json()
                    sys.exit()
                else:
                    clientside_test_result["tc2_can_get_message_from_server"] = True
                    write_json()
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
                    client_socket.send(data)

                else:
                    msg = msg.encode("utf-8")
                    client_socket.send(msg)
                clientside_test_result["tc3_can_send_message_to_server"] = True
                write_json()
                sys.stdout.flush()


def write_json():
    with open('clientside_testcase_result.txt', 'w') as f:
        json.dump(clientside_test_result, f)


if __name__ == "__main__":
    chat_client()

