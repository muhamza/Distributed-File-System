import socket
import os
import threading
import queue
import time
from random import randint

# -----------------------------------------------------------------------------------------------------------------------
# Threads Classes

class ServerListeningThread(threading.Thread):
    def __init__(self, server, serverLock, globalLock, globalDirectory, serverConnected, dir_q):
        threading.Thread.__init__(self)
        self.server = server
        self.serverLock = serverLock
        self.globalLock = globalLock
        self.globalDirectory = globalDirectory
        self.serverConnected = serverConnected
        self.dir_q = dir_q

    def run(self):
        while True:
            acceptServer, address = self.server.accept()
            self.serverLock.acquire(True)
            bool = InConnectedList(address, self.serverConnected)
            self.serverLock.release()
            if bool:
                acceptServer.close()
            else:
                print('Listening Connection Successful with Server: ', address)
                csoc = [address[0], address[1], acceptServer]
                self.serverLock.acquire(True)
                self.serverConnected.append(csoc)
                print(self.serverConnected)
                self.serverLock.release()
                currentDirectory = ListDirectoryContentsWithDeleted(directoryPath)
                localList = StoreInList(currentDirectory)
                acceptServer.sendall(currentDirectory.encode())
                received = acceptServer.recv(1024)
                remoteDirectory = received.decode()
                remoteList = StoreInList(remoteDirectory)
                for local in localList:
                    for remote in remoteList:
                        if local[1] == '*':
                            continue
                        elif local[0] == remote[0] and remote[1] == '*':
                            oldFileName = local[0] + ' ' + local[1]
                            newFileName = local[0] + ' *'
                            os.rename(oldFileName, newFileName)
                        elif local[0] == remote[0] and int(local[1]) < int(remote[1]):
                            print(local, remote)
                            oldFileName = local[0] + ' ' + local[1]
                            newFileName = remote[0] + ' ' + remote[1]
                            RequestFile(oldFileName, newFileName, acceptServer, self.serverConnected, self.serverLock, self.globalDirectory, self.globalLock)
                try:
                    serverConnThread = ServerConnectionThread(csoc, self.globalLock, self.globalDirectory, acceptServer,
                                                              self.serverLock, self.serverConnected, self.dir_q)
                    serverConnThread.start()
                    serverLock.acquire(True)
                    length = len(serverConnected)
                    if length == 2:
                        DeleteFiles()
                    serverLock.release()
                except:
                    print("Error: UNABLE TO START UPDATE DIRECTORY THREAD! listening")


class ServerConnectionThread(threading.Thread):
    def __init__(self, address, globalLock, globalDirectory, filedescriptor, serverLock, serverConnected, dir_q):
        threading.Thread.__init__(self)
        self.address = address
        self.globalLock = globalLock
        self.globalDirectory = globalDirectory
        self.filedescriptor = filedescriptor
        self.serverLock = serverLock
        self.serverConnected = serverConnected
        self.dir_q = dir_q

    def run(self):
        while True:
            # try:
                data = self.filedescriptor.recv(1024)
                #--#print('data: ', data)
                receivedData = data.decode()
                print('receivedData', receivedData)
                if receivedData == '':
                    print('Server Disconnected!')
                    self.serverLock.acquire(True)
                    UpdateServerConnectedList(self.address, self.serverConnected)
                    self.serverLock.release()
                    Update2(self.globalDirectory, self.globalLock, self.serverConnected, self.serverLock)
                    break
                else:
                    tokens = receivedData.split(' ', 1)
                    if tokens[0] == 'updateDirectory' and len(tokens) == 2:
                        # create new Global List and append tokens[1]
                        directory = ListDirectoryContents(directoryPath)
                        self.globalLock.acquire(True)
                        self.globalDirectory.clear()
                        StoreInGlobalDirectory(directory, 'self', self.globalDirectory)
                        StoreInGlobalDirectory(tokens[1], self.filedescriptor, self.globalDirectory)
                        self.globalLock.release()

                        # send own Directory List to all connected servers
                        UpdateAllServersGlobalLists(directory, self.serverConnected, self.serverLock)
                    elif tokens[0] == 'update2' and len(tokens) == 2:           #update globalDirectory on server shutdown
                        self.globalLock.acquire(True)
                        StoreInGlobalDirectory(tokens[1], self.filedescriptor, self.globalDirectory)
                        self.globalLock.release()
                    elif tokens[0] == 'create' and len(tokens) == 2:
                        self.filedescriptor.sendall('ready zyxtrecx'.encode())
                        response = self.filedescriptor.recv(1024)
                        fileData = ''
                        while True:
                            response = response.decode()
                            if response.endswith('zyxtrecx'):
                                response = response[:-8]
                                fileData = fileData + response
                                break
                            fileData = fileData + response
                            response = self.filedescriptor.recv(1024)
                        #--#print('fileData : ', fileData)
                        fd = open(tokens[1], 'w')
                        fd.write(fileData)
                        fd.close()
                        print('file %s created' % tokens[1])
                        time.sleep(0.5) #test
                        UpdateDirectory(self.serverConnected, self.serverLock, self.globalDirectory,
                                        self.globalLock)
                    elif tokens[0] == 'delete' and len(tokens) == 2:
                        fileName = tokens[1].rsplit(' ')
                        newFileName = fileName[0] + ' *'
                        os.rename(tokens[1], newFileName)
                        UpdateDirectory(self.serverConnected, self.serverLock, self.globalDirectory,
                                        self.globalLock)
                    elif tokens[0] == 'update' and len(tokens) == 2:
                        self.globalLock.acquire(True)
                        StoreInGlobalDirectory(tokens[1], self.filedescriptor, self.globalDirectory)
                        self.globalLock.release()
                    elif tokens[0] == 'download' and len(tokens) == 2:
                        # check if it has the file
                        print('tokens[0] ServerThread: ', tokens[0])
                        with open(tokens[1], 'rb') as fd:
                            load = fd.read(1024)
                            while load:
                                #--#print(load)
                                self.filedescriptor.sendall(load)
                                load = fd.read(1024)
                            fd.close()
                            self.filedescriptor.sendall('zyxtrecx'.encode())
                    elif tokens[0] == 'upload' and len(tokens) == 2:
                        print('tokens[0] ServerThread: ', tokens[0])
                        oldFileName = tokens[1]
                        file = oldFileName.rsplit(' ')
                        version = int(file[1])
                        version = version + 1
                        newFileName = file[0] + ' ' + str(version)
                        os.rename(oldFileName, newFileName)
                        self.filedescriptor.sendall('ready zyxtrecx'.encode())
                        response = self.filedescriptor.recv(1024)
                        fileData = ''
                        while True:
                            response = response.decode()
                            if response.endswith('zyxtrecx'):
                                response = response[:-8]
                                fileData = fileData + response
                                break
                            fileData = fileData + response
                            response = self.filedescriptor.recv(1024)
                        fd = open(newFileName, 'w')
                        fd.write(fileData)
                        fd.close()
                        time.sleep(0.5)  # test
                        UpdateDirectory(self.serverConnected, self.serverLock, self.globalDirectory,
                                        self.globalLock)
                    else:
                        fileData = ''
                        while True:
                            if data.decode().endswith('zyxtrecx'):
                                fileData = fileData + data.decode()
                                break
                            else:
                                fileData = fileData + data.decode()
                                data = self.filedescriptor.recv(1024)
                        self.dir_q.put(fileData)
            # except:
            #     print('Server Disconnected!')
            #     self.filedescriptor.close()
            #     break


class ClientListeningThread(threading.Thread):
    def __init__(self, client, clientLock, clientConnected, serverConnected, serverLock, globalLock, globalDirectory,
                 dir_q):
        threading.Thread.__init__(self)
        self.client = client
        self.clientLock = clientLock
        self.clientConnected = clientConnected
        self.serverConnected = serverConnected
        self.serverLock = serverLock
        self.globalLock = globalLock
        self.globalDirectory = globalDirectory
        self.dir_q = dir_q

    def run(self):
        while True:
            acceptClient, address = self.client.accept()
            print('Listening Connection Successful with Client: ', address)
            csoc = [address[0], address[1], acceptClient]
            self.clientLock.acquire(True)
            self.clientConnected.append(csoc)
            #--#print(self.clientConnected)
            self.clientLock.release()
            try:
                clientConnectionThread = ClientConnectionThread(self.serverConnected, self.serverLock, self.globalLock,
                                                                self.globalDirectory, acceptClient, dir_q)
                clientConnectionThread.start()
            except:
                print("Error: UNABLE TO START Client Connection THREAD!")


class ClientConnectionThread(threading.Thread):
    def __init__(self, serverConnected, serverLock, globalLock, globalDirectory, filedescriptor, dir_q):
        threading.Thread.__init__(self)
        self.serverConnected = serverConnected
        self.serverLock = serverLock
        self.globalLock = globalLock
        self.globalDirectory = globalDirectory
        self.filedescriptor = filedescriptor
        self.dir_q = dir_q

    def run(self):
        while True:
            #try:
                data = self.filedescriptor.recv(1024)
                command = data.decode()
                if command == '':
                    print('Client Disconnected!')
                    break
                else:
                    tokens = command.split(' ', 1)

                    if tokens[0] == 'ls' and len(tokens) == 1:
                        print('tokens[0] ClientThread: ', tokens[0])
                        self.globalLock.acquire(True)
                        sendList = SendGlobalDirectory(self.globalDirectory)
                        print(self.globalDirectory)
                        self.globalLock.release()
                        if sendList == '':
                            msg = 'THERE ARE NO FILES AVAILABLE!'
                            self.filedescriptor.sendall(msg.encode())
                        else:
                            self.filedescriptor.sendall(sendList.encode())
                    elif tokens[0] == 'delete' and len(tokens) == 2:
                        self.globalLock.acquire(True)
                        fileList = SearchInGlobalDirectoryUploadDelete(tokens[1], self.globalDirectory)
                        print('fileDelete : ', fileList)
                        self.globalLock.release()
                        if fileList == 'FILE NOT AVAILABLE':
                            message = 'FILE %s CANNOT BE DELETED AS IT DOES NOT EXISTS!' % tokens[1]
                            self.filedescriptor.sendall(message.encode())
                        else:
                            for file in fileList:
                                if file[2] == 'self':
                                    oldFileName = file[0] + ' ' + file[1]
                                    newFileName = file[0] + ' *'
                                    os.rename(oldFileName, newFileName)
                                    if len(fileList) == 1:
                                        UpdateDirectory(self.serverConnected, self.serverLock, self.globalDirectory,
                                                    self.globalLock)
                                else:
                                    command = command + ' ' + file[1]
                                    file[2].sendall(command.encode())
                            self.filedescriptor.sendall('deleted'.encode())
                    elif tokens[0] == 'download' and len(tokens) == 2:
                        print('tokens[0] ClientThread: ', tokens[0])
                        self.globalLock.acquire(True)
                        file = SearchInGlobalDirectoryDownload(tokens[1], self.globalDirectory)
                        self.globalLock.release()
                        if file == 'FILE NOT AVAILABLE':
                            # send message - file not available
                            msg = ('FILE %s IS NOT AVAILABLE!' % tokens[1])
                            self.filedescriptor.sendall(msg.encode())
                        elif file[2] == 'self':
                            # send file from server
                            fileName = file[0] + ' ' + file[1]
                            with open(fileName, 'rb') as fd:
                                load = fd.read(1024)
                                while load:
                                    self.filedescriptor.sendall(load)
                                    load = fd.read(1024)
                                fd.close()
                                self.filedescriptor.sendall('zyxtrecx'.encode())
                        else:
                            command = 'reconnect ' + file[3]
                            self.filedescriptor.sendall(command.encode())
                            print('Ip of another server sent to client')
                    elif tokens[0] == 'upload' and len(tokens) == 2:
                        self.filedescriptor.sendall('ready'.encode())
                        print('waiting for file from client')
                        response = self.filedescriptor.recv(1024)
                        fileData = ''
                        while True:
                            response = response.decode()
                            if response.endswith('zyxtrecx'):
                                response = response[:-8]
                                fileData = fileData + response
                                break
                            else:
                                fileData = fileData + response
                                response = self.filedescriptor.recv(1024)
                        #--#print('response from client ', fileData)
                        self.globalLock.acquire(True)
                        fileList = SearchInGlobalDirectoryUploadDelete(tokens[1], self.globalDirectory)
                        print('file', fileList)
                        self.globalLock.release()
                        if fileList == 'FILE NOT AVAILABLE' or fileList is None:    # FILE CREATION
                            fileName = tokens[1] + ' 1'         # create file on 'self' server
                            fd = open(fileName, 'w')
                            fd.write(fileData)
                            fd.close()
                            print('file created')

                            message = 'create ' + fileName      # create file on other server
                            fileData = fileData + 'zyxtrecx'
                            #--#print('fileData imp: ', fileData)

                            isFound = False
                            conn = []
                            serverLock.acquire(True)
                            length = len(serverConnected)
                            if length > 0:
                                index = randint(0, length - 1)
                                conn = serverConnected[index]
                                isFound = True
                            serverLock.release()

                            if isFound:
                                print('Sending file %s to Server %s' % (tokens[1], conn[0]))
                                conn[2].sendall(message.encode())
                                data = self.dir_q.get()
                                data = data[:-9]
                                print('recveived from server : ', data)
                                if data == 'ready':
                                    conn[2].sendall(fileData.encode())
                                    print('File %s sent to Server %s' % (tokens[1], conn[0]))
                            else:
                                UpdateDirectory(self.serverConnected, self.serverLock, self.globalDirectory, self.globalLock)
                        else:
                            for file in fileList:
                                if file[2] == 'self':
                                    oldFileName = file[0] + ' ' + file[1]
                                    version = int(file[1])
                                    version = version + 1
                                    newFileName = file[0] + ' ' + str(version)
                                    os.rename(oldFileName, newFileName)
                                    fd = open(newFileName, 'w')
                                    fd.write(fileData)
                                    fd.close()
                                    print('file uploaded on server')
                                    if len(fileList) == 1:
                                        UpdateDirectory(self.serverConnected, self.serverLock, self.globalDirectory,
                                                        self.globalLock)
                                else:
                                    fileData = fileData + 'zyxtrecx'
                                    print('file upload command sent to another server')
                                    command = command + ' ' + file[1]
                                    file[2].sendall(command.encode())
                                    data = self.dir_q.get()
                                    data = data[:-9]
                                    print('queue read: ', data)
                                    print('received confirmation for sending file to another server')
                                    if data == 'ready':
                                        file[2].sendall(fileData.encode())
                                        print('file uploaded on another server')
                    elif tokens[0] == 'create' and len(tokens) == 2:
                        self.globalLock.acquire(True)
                        isFound = IsInGlobalDirectory(tokens[1], self.globalDirectory)
                        self.globalLock.release()
                        if isFound == True:
                            self.filedescriptor.sendall('found'.encode())
                        else:
                            self.filedescriptor.sendall('notfound'.encode())
                    elif tokens[0] == 'refresh' and len(tokens) == 1:
                        UpdateDirectory(self.serverConnected, self.serverLock, self.globalDirectory, self.globalLock)
                    else:
                        msg = ('INVALID COMMAND!')
                        self.filedescriptor.sendall(msg.encode())
            # except:
            #     print('Client Disconnected!')
            #     self.filedescriptor.close()
            #     break


# ----------------------------------------------------------------------------------------------------------------------
# Methods

def InConnectedList(address, list):                                 # checks if an IP Address is already in the Connected List
    size = len([item for item in list if address[0] == item[0]])
    if size > 0:
        return True
    else:
        return False


def UpdateServerConnectedList(conn, serverConnected):
    for item in serverConnected:
        if item[0] == conn[0] and item[1] == conn[1]:
            serverConnected.remove(item)
            print(serverConnected)
            break

def ListDirectoryContents(path):                                    # server gets its own List Contents and return string
    directoryList = [file for file in os.listdir(path)]
    sendList = ''
    for item in directoryList:
        if not item.endswith('*'):
            sendList = sendList + item + ', '
    sendList = sendList[:-2]
    return sendList

def ListDirectoryContentsWithDeleted(path):                         # server gets its own List Contents and return string
    directoryList = [file for file in os.listdir(path)]
    sendList = ''
    for item in directoryList:
        sendList = sendList + item + ', '
    sendList = sendList[:-2]
    return sendList

def StoreInGlobalDirectory(string, fd,
                           globalDirectory):                        # server receives a string and stores in globalDirectory [filename, version, fd]
    if len(string) > 0:
        retList = (string.split(', '))
        for item in retList:
            file = item.rsplit(' ')
            if fd == 'self':
                add = [file[0], file[1], fd, fd]                    #[FileName, version, fd, ip]
            else:
                ip, port = fd.getpeername()
                add = [file[0], file[1], fd, ip]
            globalDirectory.append(add)


def SearchInGlobalDirectoryDownload(fileName, globalDirectory):     # searches the globalDirectory, returns fd with the latest version, if file is available
    if len(globalDirectory) > 0:
        maximum = 0
        file = object
        for item in globalDirectory:
            if item[0] == fileName and int(item[1]) > maximum:
                maximum = int(item[1])
                file = item
            elif item[0] == fileName and int(item[1]) == maximum and item[2] == 'self':
                maximum = int(item[1])
                file = item
        if maximum == 0:
            return 'FILE NOT AVAILABLE'
        else:
            print('return file : ', file)
            return file
    else:
        print('THERE IS NO FILE IN THE GLOBAL DIRECTORY!')

def SearchInGlobalDirectoryUploadDelete(fileName, globalDirectory):       # searches the globalDirectory, returns List of files
    returnList = []
    if len(globalDirectory) > 0:
        for item in globalDirectory:
            if item[0] == fileName:
                returnList.append(item)
        if len(returnList) == 0:
            return 'FILE NOT AVAILABLE'
        else:
            return returnList
    else:
        print('THERE IS NO FILE IN THE GLOBAL DIRECTORY!')


def IsInGlobalDirectory(fileName, globalDirectory):                 # searches the globalDirectory, returns TRUE if file is available
    for item in globalDirectory:
        if item[0] == fileName:
            return True
    return False


def SendGlobalDirectory(globalDirectory):                           # to send the unique global directory to client; returns string
    sendList = ''
    if len(globalDirectory) > 0:
        output = []
        for item in globalDirectory:
            if item[0] not in output:
                output.append(item[0])
                sendList = sendList + item[0] + ', '
        sendList = sendList[:-2]
    return sendList

def SendGlobalDirectoryUnused(globalDirectory):                           # to send the global directory to client; returns string
    sendList = ''
    if len(globalDirectory) > 0:
        for item in globalDirectory:
            sendList = sendList + item[0] + ' ' + item[1] + ', '
            # sendList = sendList + item[0] + ', '                   #orignal version
        sendList = sendList[:-2]
    return sendList


def UpdateDirectory(connectedList, serverLock, globalList,
                    globalLock):                                    # sends messages to other servers to update their Global Lists. Client Connection thread runs it.
    directory = ListDirectoryContents(directoryPath)
    print('directory updateDirectory ', directory)
    globalLock.acquire(True)
    globalList.clear()
    StoreInGlobalDirectory(directory, 'self', globalList)
    globalLock.release()

    # get own Directory List
    message = 'updateDirectory '
    directory2 = message + directory

    # send own Directory List to all other connected servers
    serverLock.acquire(True)
    if len(serverConnected) == 0:
        serverLock.release()
        return
    else:
        for items in connectedList:
            items[2].sendall(directory2.encode())
    serverLock.release()


def UpdateAllServersGlobalLists(directory, connectedList, serverLock):
    message = 'update '
    directory2 = message + directory
    # send own Directory List to all other connected servers
    serverLock.acquire(True)
    for items in connectedList:
        items[2].sendall(directory2.encode())
    serverLock.release()

def Update2(globalDirectory, globalLock, connectedList, serverLock):
    directory = ListDirectoryContents(directoryPath)
    globalLock.acquire(True)
    globalDirectory.clear()
    StoreInGlobalDirectory(directory, 'self', globalDirectory)
    globalLock.release()

    message = 'update2 ' + directory
    serverLock.acquire(True)
    if len(connectedList) == 0:
        serverLock.release()
        return
    else:
        for conn in connectedList:
            conn[2].sendall(message.encode())
    serverLock.release()

def StoreInList(string):                                              # stores filenames and version in list and return them
    returnList = []
    if len(string) > 0:
        retList = (string.split(', '))
        for item in retList:
            file = item.rsplit(' ')
            add = [file[0], file[1]]
            returnList.append(add)
    return returnList

def RequestFile(oldFileName, newFileName, socketfd, serverConnected, serverLock, globalDirectory, globalLock):
    message = 'download ' + newFileName
    socketfd.sendall(message.encode())
    receive = socketfd.recv(1024)
    os.rename(oldFileName, newFileName)
    with open(newFileName, 'wb') as fd:
        while True:
            if receive.decode().endswith('zyxtrecx'):
                receive = receive[:-8]
                fd.write(receive)
                break
            fd.write(receive)
            receive = socketfd.recv(1024)
        fd.close()
    #UpdateDirectory(serverConnected, serverLock, globalDirectory, globalLock)

def DeleteFiles():
    for file in os.listdir(directoryPath):
        if file.endswith("*"):
            os.remove(file)

# ----------------------------------------------------------------------------------------------------------------------

# Main Method START
serverLock = threading.Lock()
clientLock = threading.Lock()
globalLock = threading.Lock()

directoryPath = '/home/test/Desktop/MyWorkspace'
os.chdir(directoryPath)

dir_q = queue.Queue()

toConnect = [['192.168.0.104', 9999], ['192.168.0.107', 9999]]      #server ip's, to connect to
serverConnected = []
clientConnected = []
globalDirectory = []

# Listening to Server Connection Requests
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

port = 9999
server.bind(('', port))
print("Socket bound to %s" % (port))
server.listen(5)
try:
    serverThreadListen = ServerListeningThread(server, serverLock, globalLock, globalDirectory, serverConnected, dir_q)
    serverThreadListen.start()
except:
    print("Error: UNABLE TO START SERVER LISTENING THREAD!")

# Listening to Client Connection Requests
client = socket.socket()
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

port = 8888
client.bind(('', port))
print("Socket bound to %s" % (port))
client.listen(5)
try:
    clientThreadListen = ClientListeningThread(client, clientLock, clientConnected, serverConnected, serverLock,
                                               globalLock, globalDirectory, dir_q)
    clientThreadListen.start()
except:
    print("Error: UNABLE TO START CLIENT LISTENING THREAD!")

# Global Directory Appending
globalLock.acquire(True)
currentDirectory = ListDirectoryContents(directoryPath)
StoreInGlobalDirectory(currentDirectory, 'self', globalDirectory)
globalLock.release()

# Connection Requests
for soc in toConnect:
    serverLock.acquire(True)
    bool = InConnectedList(soc, serverConnected)
    serverLock.release()
    if bool:
        continue
    else:
        print('Connecting with Server: ', soc)
        serverEnd = socket.socket()
        serverEnd.settimeout(3)
        try:
            ret = serverEnd.connect_ex((soc[0], soc[1]))
            serverEnd.settimeout(None)
            if ret == 0:
                csoc = [soc[0], soc[1], serverEnd]
                serverLock.acquire(True)
                serverConnected.append(csoc)
                print('Connection Request Successful')
                print(serverConnected)
                serverLock.release()
                currentDirectory = ListDirectoryContentsWithDeleted(directoryPath)
                localList = StoreInList(currentDirectory)
                serverEnd.sendall(currentDirectory.encode())
                received = serverEnd.recv(1024)
                remoteDirectory = received.decode()
                remoteList = StoreInList(remoteDirectory)
                for local in localList:
                    for remote in remoteList:
                        if local[1] == '*':
                            continue
                        elif local[0] == remote[0] and remote[1] == '*':
                            oldFileName = local[0] + ' ' + local[1]
                            newFileName = local[0] + ' *'
                            os.rename(oldFileName, newFileName)
                        elif local[0] == remote[0] and int(local[1]) < int(remote[1]):
                            print(local, remote)
                            oldFileName = local[0] + ' ' + local[1]
                            newFileName = remote[0] + ' ' + remote[1]
                            RequestFile(oldFileName, newFileName, serverEnd, serverConnected, serverLock, globalDirectory, globalLock)
                try:
                    serverConnThread = ServerConnectionThread(csoc, globalLock, globalDirectory, serverEnd, serverLock,
                                                              serverConnected, dir_q)
                    serverConnThread.start()
                    time.sleep(0.5)
                    UpdateDirectory(serverConnected, serverLock, globalDirectory, globalLock)
                    serverLock.acquire(True)
                    length = len(serverConnected)
                    if length == 2:
                        DeleteFiles()
                    serverLock.release()
                except:
                    print("Error: UNABLE TO START UPDATE DIRECTORY THREAD! connection")
        except socket.error:
            print("Error: UNABLE TO CONNECT TO SERVER " + soc[0], soc[1])

# time.sleep(10)
# globalLock.acquire(True)
# print(globalDirectory)
# globalLock.release()
