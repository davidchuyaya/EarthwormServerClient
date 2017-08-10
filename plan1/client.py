import os
import socket
import const

HOST = "localhost"
SAC_FILE_DIR = "clientSAC"
SAC_LIST_FILE = SAC_FILE_DIR + "/saclist"

with open(SAC_LIST_FILE, "r") as sacList:
    # Ignore the 1st line
    next(sacList)
    for sacFileName in sacList.read().splitlines():

        # Create a TCP/IP socket
        with socket.create_connection((HOST, const.PORT)) as sock:
            print("Connected to server")

            sacFileNameWithPath = SAC_FILE_DIR + "/" + sacFileName

        # Wait for server to tell us what to do
            while True:
                requestFromServer = sock.recv(32)

                if requestFromServer == const.REQUEST_NAME:
                    sock.send(sacFileName.encode())
                    print("sent name")
                if requestFromServer == const.REQUEST_SIZE:
                    sock.send(int.to_bytes(os.path.getsize(sacFileNameWithPath), length=const.MAX_DATA_SIZE, byteorder="big"))
                    print("sent size")
                if requestFromServer == const.REQUEST_FILE:
                    with open(sacFileNameWithPath, "rb") as sacFile:
                        # Send file in chunks according to MAX_DATA_SIZE
                        while True:
                            bytesToSend = sacFile.read(const.MAX_DATA_SIZE)
                            if not bytesToSend:
                                break
                            sock.send(bytesToSend)
                        print("Sent SAC file: " + sacFileName)
                if requestFromServer == const.REQUEST_END:
                    break
