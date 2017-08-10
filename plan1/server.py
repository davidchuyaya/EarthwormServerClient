import os
import socket
import subprocess
import sys
import const

SAC_DIR = "serverSAC"
TANK_DIR = "serverTank"
TBUF_PATH = TANK_DIR + "/tracebuf"
MAX_CONNECTIONS = 1
NUM_TBUF_COMPRESS = 10

# Make directories if necessary
os.makedirs(SAC_DIR, exist_ok=True)
os.makedirs(TANK_DIR, exist_ok=True)

# Begin listening for connections
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", const.PORT))
sock.listen(MAX_CONNECTIONS)

print("server listening")

while True:
    sacFilesReceived = 0
    numTankFiles = 0

    connection, clientAddress = sock.accept()
    try:
        print("connection from ", clientAddress)

        # Get the name of the file
        connection.send(const.REQUEST_NAME)
        name = connection.recv(const.MAX_DATA_SIZE).decode()
        filePath = SAC_DIR + "/" + name
        sacFile = open(filePath, "wb")
        print("name: " + name)

        # Get the size of the file
        connection.send(const.REQUEST_SIZE)
        size = int.from_bytes(connection.recv(const.MAX_DATA_SIZE), byteorder="big")
        print("size: " + str(size))

        # Get the actual file
        connection.send(const.REQUEST_FILE)
        receivedBytes = 0
        while receivedBytes < size:
            # write received data to file
            data = connection.recv(const.MAX_DATA_SIZE)
            sacFile.write(data)
            receivedBytes += sys.getsizeof(data)
            print("received: " + str(receivedBytes))

        sacFile.close()
        sacFilesReceived += 1

        # Close the connection
        connection.send(const.REQUEST_END)

        # Converts from SAC file to Tracebuf
        subprocess.Popen("sac2tb -a " + filePath + " " + TBUF_PATH)

        if sacFilesReceived == NUM_TBUF_COMPRESS:
            subprocess.Popen("remux_tbuf " + TBUF_PATH + " " + TANK_DIR + "/" + str(numTankFiles) + ".tnk")
            open(TBUF_PATH, "w").close()    # Clear tbuf after creating tank file
            numTankFiles += 1
            sacFilesReceived = 0
    finally:
        connection.close()
