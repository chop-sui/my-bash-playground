#!/bin/python

import signal
import os
import sys
import select
import struct
import csv
import logging

db_filename = "/tmp/cald_db.csv"
logging.basicConfig(filename='/tmp/cald_err.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# command format
def encode_cmd_size(size: int) -> bytes:
    return struct.pack("<|", size)


def decode_cmd_size(size_bytes: bytes) -> int:
    return struct.unpack("<|", size_bytes)[0]


def create_cmd(content: bytes) -> bytes:
    size = len(content)
    return encode_cmd_size(size) + content


# Use this variable for your loop
daemon_quit = False


# Do not modify or remove this handler
def quit_gracefully(signum, frame):
    global daemon_quit
    daemon_quit = True


def init_db(path):
    with open(db_filename, 'w') as csv_file:
        csv_writer = csv.writer(csv_file)


def add_event(date, event, description):
    row = [date, event, description]

    with open(db_filename, 'a') as write_file:
        writer = csv.writer(write_file)
        writer.writerow(row)


def delete_event(date, event):
    with open(db_filename, 'r+') as read_file:
        reader = csv.reader(read_file)
        rows = [row for row in reader if date not in row and event not in row]
        read_file.seek(0)
        read_file.truncate()
        writer = csv.writer(read_file)
        writer.writerows(rows)


def update_event(date, old_event, new_event, description):
    rows = list()
    with open(db_filename, 'r+') as read_file:
        reader = csv.reader(read_file)
        for row in reader:
            rows.append(row)
            if date in row and old_event in row:
                row[1] = new_event
                if description is not None:
                    row[2] = description
        read_file.seek(0)
        read_file.truncate()
        writer = csv.writer(read_file)
        writer.writerows(rows)


def start_writer():
    FIFO_NAME = '/tmp/cald_pipe'

    fifo = os.open(FIFO_NAME, os.O_WRONLY)
    try:
        while True:
            enter_cmd = input()
            content = enter_cmd.encode("utf8")
            cmd = create_cmd(content)
            os.write(fifo, cmd)
    except KeyboardInterrupt:
        print("\nTERMINATED")
    finally:
        os.close(fifo)


def get_cmd(fifo: int) -> str:
    """Get a cmd from the named pipe"""
    cmd_size_bytes = os.read(fifo, 4)
    cmd_size = decode_cmd_size(cmd_size_bytes)
    cmd_content = os.read(fifo, cmd_size).decode("utf8")
    return cmd_content


def start_reader():
    # Set up the named pipe and poll for new commands
    FIFO_NAME = '/tmp/cald_pipe'
    os.mkfifo(FIFO_NAME)
    try:
        fifo = os.open(FIFO_NAME, os.O_RDONLY | os.O_NONBLOCK)
        try:
            poll = select.poll()
            poll.register(fifo, select.POLLIN)
            try:
                while True:
                    if (fifo, select.POLLIN) in poll.poll(2000):
                        cmd = get_cmd(fifo)
                        print(cmd)
                    else:
                        print("No data passed")
            finally:
                poll.unregister(fifo)
        finally:
            os.close(fifo)
    finally:
        os.remove(FIFO_NAME)


def handle_cmd(cmd):
    try:
        data = cmd.split()
        date = data[1]
        event = data[2]
        description = None

        if cmd.startswith('ADD'):
            if data.size() == 4:
                description = data[3]
                add_event(date, event, description)

        elif cmd.startswith('DEL'):
            delete_event(date, event)

        elif cmd.startswith('UPD'):
            new_event = data[3]
            if data.size() == 5:
                description = data[4]
            update_event(date, event, new_event, description)

        else:
            raise ValueError("Invalid Command Arguments Received")
    except IndexError as e:
        logger.error(e)
        print("Parsing Error")
    except ValueError as e:
        logger.error(e)
        print("Exception raised >>")


def run():
    # Do not modify or remove this function call
    signal.signal(signal.SIGINT, quit_gracefully)

    # Call your own functions from within
    # the run() function
    start_reader()
    start_writer()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        db_path = sys.argv[1]
    else:
        db_path = os.path.dirname(os.path.realpath(__file__))
    # TODO Exception handling for different number of command line arguments
    init_db(db_path)
    run()
