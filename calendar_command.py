import os
import sys
import logger
import csv

DB_INDEX_FILE = '/tmp/calendar_link'


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


def read_db():
    try:
        with open(DB_INDEX_FILE) as fp:
            db_file = fp.read()
            # Read DB
    except OSError as e:
        # Output to stderr
        print("Unable to process calendar database")

def get_events_by_dates(dates):
    events = list()
    with open(db_file) as fp:
        reader = csv.reader(fp)
        for row in reader:
            for date in dates:
                if date in row:
                    events.append(row)
    print(events)

def get_events_by_interval(interval):
    events = list()
    with open(db_file) as fp:
        reader = csv.reader(fp)
        for row in reader:
            if row[0] >= interval[0] and row[0] <= interval[1]:
                events.append(row)
    print(events)

def get_events_by_name(name):
    events = list()
    with open(db_file) as fp:
        reader = csv.reader(fp)
        for row in reader:
            if row[1].startswith(name):
                events.append(row)
    print(events)

def run():
    # YOUR CODE HERE
    pass

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        if sys.argv[1] == "GET":
            if sys.argv[2] == "DATE":
                try:
                    dates = []
                    while i < len(sys.argv):
                        dates.append(datetime.datetime.strptime(sys.argv[i], "%Y-%m-%d"))
                        i += 1
                except ValueError:
                    #stderr
                get_events_by_dates(dates)
            elif sys.argv[2] == "INTERVAL":

            elif sys.argv[2] == "NAME":

            else:
                #stderr
    run()
