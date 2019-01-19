import socket
import os

def ConnectToServer(port):
    serverIps = ['192.168.0.105', '192.168.0.107', '192.168.0.104']     #list of server ip's that the client will try in order.
    for ip in serverIps:
        server = socket.socket()
        server.settimeout(1)
        ret = server.connect_ex((ip, port))
        server.settimeout(None)
        if ret == 0:
            print('Connected With : ', ip)
            return server
    return 'NO SERVERS AVAILABLE!'

def ReinitiateConnection(server, port):
    server.close()
    server = ConnectToServer(port)
    if server == 'NO SERVERS AVAILABLE!':
        print('NO SERVERS AVAILABLE!')
        exit(0)
    return server

#Main ------------------------------------------------------------------------------------------------------------------

clientDirectory = '/home/test/Desktop/ClientFolder'
os.chdir(clientDirectory)
port = 8888

server = ConnectToServer(port)
if server == 'NO SERVERS AVAILABLE!':
    print('NO SERVERS AVAILABLE!')
else:
    while True:
        #try:
            userInput = input('Enter Command: ')
            tokens = userInput.split(' ', 1)
            print('userInput: ', userInput)

            if tokens[0] == 'quit' and len(tokens) == 1:
                break
            elif tokens[0] == 'ls' and len(tokens) == 1:
                server.sendall(('ls').encode())
                data = server.recv(1024)
                if data.decode() == '':
                    server = ReinitiateConnection(server, port)
                    continue
                dirList = data.decode()
                print(dirList)
            elif tokens[0] == 'delete' and len(tokens) == 2:
                server.sendall(userInput.encode())
                receive = server.recv(1024)
                if receive.decode() == '':
                    server = ReinitiateConnection(server, port)
                    continue
                error = 'FILE %s CANNOT BE DELETED AS IT DOES NOT EXISTS!' % tokens[1]
                success = 'FILE %s DELETED!' % tokens[1]
                if receive.decode() == error:
                    print(error)
                elif receive.decode() == 'deleted':
                    print(success)
            elif tokens[0] == 'download' and len(tokens) == 2:
                server.sendall(userInput.encode())
                chunk = server.recv(1024)
                if chunk.decode() == '':
                    server = ReinitiateConnection(server, port)
                    continue
                error = 'FILE %s IS NOT AVAILABLE!' % tokens[1]
                decodedData = chunk.decode()
                tok = decodedData.split(' ', 1)
                if tok[0] == 'reconnect':
                    server.close()
                    server = socket.socket()
                    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    ret = server.connect((tok[1], port))
                    print('Connected With : ', tok[1])
                    server.sendall(userInput.encode())
                    chunk = server.recv(1024)
                    error = 'FILE %s IS NOT AVAILABLE!' % tokens[1]
                    decoded = chunk.decode()
                    if decoded == error:
                        print(error)
                    else:
                        with open(tokens[1], 'wb') as fd:
                            while True:
                                if chunk.decode().endswith('zyxtrecx'):
                                    chunk = chunk[:-8]
                                    fd.write(chunk)
                                    break
                                fd.write(chunk)
                                chunk = server.recv(1024)
                            fd.close()
                        print('File %s Downloaded!' % tokens[1])
                        before = os.stat(tokens[1])[8]
                        os.system("gedit %s" % tokens[1])
                        after = os.stat(tokens[1])[8]
                        if before == after:
                            print('FILE %s NOT UPLOADED ON SERVER, SINCE IT WAS NOT CHANGED.' % tokens[1])
                            continue
                        else:
                            message = 'upload ' + tokens[1]
                            server.sendall(message.encode())
                            response = (server.recv(1024)).decode()
                            if response == 'ready':
                                fd = open(tokens[1], 'rb')
                                load = fd.read(1024)
                                while load:
                                    server.sendall(load)
                                    load = fd.read(1024)
                                fd.close()
                                server.sendall('zyxtrecx'.encode())
                                print('File %s Uploaded on Server!' % tokens[1])
                elif decodedData == error:
                    print(error)
                else:
                    with open(tokens[1], 'wb') as fd:
                        while True:
                            if chunk.decode().endswith('zyxtrecx'):
                                chunk = chunk[:-8]
                                fd.write(chunk)
                                break
                            fd.write(chunk)
                            chunk = server.recv(1024)
                        fd.close()
                    print('File %s Downloaded!' % tokens[1])
                    before = os.stat(tokens[1])[8]
                    os.system("gedit %s" % tokens[1])
                    after = os.stat(tokens[1])[8]
                    if before == after:
                        print('FILE %s NOT UPLOADED ON SERVER, SINCE IT WAS NOT CHANGED.' % tokens[1])
                        continue
                    else:
                        message = 'upload ' + tokens[1]
                        server.sendall(message.encode())
                        response = (server.recv(1024)).decode()
                        if response == 'ready':
                            fd = open(tokens[1], 'rb')
                            load = fd.read(1024)
                            while load:
                                server.sendall(load)
                                load = fd.read(1024)
                            fd.close()
                            server.sendall('zyxtrecx'.encode())
                            print('File %s Uploaded on Server!' % tokens[1])
            elif tokens[0] == 'create' and len(tokens) == 2:
                server.sendall(userInput.encode())
                data = server.recv(1024)
                if data.decode() == '':
                    server = ReinitiateConnection(server, port)
                    continue
                if data.decode() == 'found':
                    print('FILE CANNOT BE CREATED AS A FILE WITH THE NAME %s ALREADY EXISTS!' % tokens[1])
                else:
                    fd = open(tokens[1], 'w+')
                    os.system("gedit %s" % tokens[1])
                    message = 'upload ' + tokens[1]
                    server.sendall(message.encode())
                    response = (server.recv(1024)).decode()
                    if response == 'ready':
                        fd = open(tokens[1], 'rb')
                        load = fd.read(1024)
                        while load:
                            server.sendall(load)
                            load = fd.read(1024)
                        fd.close()
                        server.sendall('zyxtrecx'.encode())
                        print('File %s Uploaded on Server!' % tokens[1])
            elif tokens[0] == 'upload' and len(tokens) == 2:
                if os.path.isfile(tokens[1]):
                    server.sendall(userInput.encode())
                    response = (server.recv(1024)).decode()
                    if response == '':
                        server = ReinitiateConnection(server, port)
                        continue
                    print('reponse ', response)
                    if response == 'ready':
                        fd = open(tokens[1], 'rb')
                        load = fd.read(1024)
                        while load:
                            server.sendall(load)
                            load = fd.read(1024)
                        fd.close()
                        server.sendall('zyxtrecx'.encode())
                        print('File %s Uploaded on Server!' % tokens[1])
                else:
                    print('FILE %s DOES NOT EXISTS!' % tokens[1])
            elif tokens[0] == 'refresh' and len(tokens) == 1:
                server.sendall(userInput.encode())
            else:
                print('INVALID COMMAND!')
        # except socket.error as e:
        #     print('Exception : ', e)




