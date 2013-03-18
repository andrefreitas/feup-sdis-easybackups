"""
This class describes a peer computer. The peer have a home directory
that is where the backups are store and the temporary files, ie. chunks
that were generated to send to another peer in the network.
"""
import os
import socket
import struct
import re
from file import File
from threading import Thread

BACKUP_DIR="backup"
TEMP_DIR="temp"
SHELL_PORT=8383

class Peer:
    def __init__(self, home_dir,mc_address,mc_port,mdb_address,mdb_port,mdr_address,mdr_port,shell_port=SHELL_PORT):
        self.home_dir=home_dir
        self.init_home_dir()
        self.mc=self.create_multicast_socket(mc_address, mc_port)
        self.mdb=self.create_multicast_socket(mdb_address, mdb_port)
        self.mdr=self.create_multicast_socket(mdr_address, mdr_port)
        self.shell=self.create_socket(shell_port)
        
        
    def init_home_dir(self):
        backup_path=self.home_dir+"/"+BACKUP_DIR
        if(not os.path.exists(backup_path)):
            os.makedirs(backup_path)
            
        temp_path=self.home_dir+"/"+TEMP_DIR
        if(not os.path.exists(temp_path)):
            os.makedirs(temp_path)    
    
    def listen_shell(self):    
        while True:
            message = self.shell.recvfrom(8192)[0]      
            self.handle_shell_request(message)

    
    def listen_all(self):
        shell = Thread(target=self.listen_shell, args=())
        mc = Thread(target=self.listen, args=(self.mc,))
        mdb = Thread(target=self.listen, args=(self.mdb,))
        mdr = Thread(target=self.listen, args=(self.mdr,))
        shell.start()
        mdb.start()       
        mc.start()
        mdr.start()
        shell.join()
        mdb.join()
        mc.join()
        mdr.join()
    
    def create_multicast_socket(self,multicast_address,multicast_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', multicast_port))
        mreq = struct.pack("4sl", socket.inet_aton(multicast_address), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return sock
    
    def create_socket(self,port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        return  s
    
    def listen(self,sock):
        while True:
            message = sock.recv(10240)
            request = Thread(target=self.handle_request, args=(message,))
            request.start()
            request.join()
            
    def handle_request(self, message):
        print message
       
    def handle_shell_request(self, message):
        print message
        args=message.split(" ")
        operation=args[0]
        if(operation=="backup"):
            file_path=args[1]
            #replication_degree=int(args[2])
            file_to_backup=File(file_path)
            file_to_backup.generate_chunks(self.home_dir+"/"+TEMP_DIR)
            
        
    def send_chunk(self, path):
        chunks={}
        f = File(path)
        dir_list = os.listdir(self.home_dir+"/"+TEMP_DIR)
        os.chdir(self.home_dir+"/"+TEMP_DIR)
        f.generate_chunks()
        i=0
        for file_name in dir_list:
            chunk_name_pattern = f.get_name()+"_"+str(i)+"\.chunk"
            match = re.search(chunk_name_pattern, file_name)
            i+=1
            if (match):
                chunks[int(match.group(1))] = file_name
                
        for j in range(len(chunks)):
            chunk_file = open(str(chunks[j]), "rb")
            self.mdb.sendall(chunk_file.read())

        
p=Peer("/home/andre/easybackup", "224.1.1.1", 5678, "224.1.1.2", 5778, "224.1.1.3", 5878)
p.listen_all()