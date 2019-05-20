# Distributed-File-System
A Distributed File System developed using system apis. The file system is completely transparent and also supports replication of files to promote availability and reliability.

# Help to run the Client and Server Programs.  

**Setting up the files on your Desktop:**  
**Note:** _Please read the **Help Document** for a pictorial help and explanation, for setting up the files._  
          _Also, read the architecture details for a better understanding of the two processes (Client and Server) and how they work._  

1. Create a text file ‘server’ on your Desktop and save the Server Code in that file.  
2. Create a text file ‘client’ on your Desktop and save the Client Code in that file.  
Make these files on all three computers that will be used as servers.  
3. Create two FOLDERS ‘MyWorkspace’ and ‘ClientFolder’ on your desktop.  
4. Create an empty file as ‘test 1’ in ‘MyWorkspace’ Folder. The servers exchange there lists when they boot up and there needs to be at least one file in the local folder.  
5. Open the client file. And Enter the IP addresses of the servers, in the serverIps list.  
6. Also change the directory path of the ‘ClientFolder’ Folder that you created in step 3 in the client file.  
7. Open the server file. And Enter the IP addresses of the servers, in the toConnect list.  
8. Also change the directory path of the ‘MyWorkspace’ Folder that you created in step 3, in the server file’s ‘directoryPath’ variable.  

**Compile and Run**  

Client:  
1. To run the client, open the terminal in linux and change directory to Desktop by typing = ‘cd Desktop’  
2. Once the folder is changed, type = ‘python3 client’. This will run the client program.  

Server:  
1. To run the server, open another terminal in linux and change directory to Desktop by typing = ‘cd Desktop’  
2. Once the folder is changed, type = ‘python3 server’. This will run the server program.  

# Commands for Client  

These are the list of commands that could be run from the client to request specific operation from the servers.  

1. **ls:** this command is used to list down the Global Contents of the distributed file system. This will list down all files that are currently available. Example use: ls  
2. **refresh:** this command is used to refresh the global directory contents. Example use: refresh  
3. **download:** this command along with the file’s name is used to request the file from the server. When the file is downloaded onto the client, it is opened with a text editor and allows the user to edit it. On closing the file, the file is uploaded back to the server. If the user has not made any changes and closes the file, it will not be uploaded onto the server. Example use: download distributed-file  
4. **create:** this command will create a new file on the client and open it in a text editor. The user can then write to it. The file will be automatically uploaded onto the servers, when the user will close the file. Example use: create distributed-file  
5. **delete:** this command can be used to delete a specific file, located anywhere on the servers. Example use: delete distributed-file  
