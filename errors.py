from datetime import datetime
import os
LOG_FILE_PATH = ""

def initiate_logs(cwd):
    global LOG_FILE_PATH
    today = datetime.today()
    date_string = str(today.hour) + ":" + str(today.minute) + "_" + str(today.month) + "." + str(today.day) + "." + str(today.year)
    LOG_FILE_PATH = os.path.join(cwd, ("logs/" + date_string + ".log"))
    
    f = open(LOG_FILE_PATH, 'a')
    f.close()


def log_error(e):
    now = datetime.now()
    time_string = str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
    f = open(LOG_FILE_PATH, 'a')
    f.write("[" + time_string + "] " + str(e) + "\n")
    f.close()

class SocketDisconnected(Exception):
    pass

class UnexpectedPacket(Exception):
    pass