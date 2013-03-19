"""
This class describes a peer computer. The peer have a home directory
that is where the backups are store and the temporary files, ie. chunks
that were generated to send to another peer in the network.
"""
import os
import socket
import struct
from file import File
from threading import Thread
from datetime import datetime

BACKUP_DIR="backup"
TEMP_DIR="temp"
SHELL_PORT=8383
VERSION="1.0"
CRLF="\r\n"

def print_message(message):
    print  "[" + datetime.now().strftime("%d/%m/%y %H:%M") + "] " + message

class Peer:
    def __init__(self, home_dir,mc_address,mc_port,mdb_address,mdb_port,mdr_address,mdr_port,shell_port=SHELL_PORT):
        self.home_dir=home_dir
        self.init_home_dir()
        self.mc=self.create_multicast_socket(mc_address, mc_port)
        self.mc_address=mc_address
        self.mc_port=mc_port
        self.mdb_address=mdb_address
        self.mdb_port=mdb_port
        self.mdr_address=mdr_address
        self.mdr_port=mdr_port
        self.mdb=self.create_multicast_socket(mdb_address, mdb_port)
        self.mdr=self.create_multicast_socket(mdr_address, mdr_port)
        self.shell_port=shell_port
        self.shell=self.create_socket(self.shell_port)
        
        
    def init_home_dir(self):
        self.backup_dir=self.home_dir+"/"+BACKUP_DIR+"/"
        if(not os.path.exists(self.backup_dir)):
            os.makedirs(self.backup_dir)
            
        self.temp_dir=self.home_dir+"/"+TEMP_DIR+"/"
        if(not os.path.exists(self.temp_dir)):
            os.makedirs(self.temp_dir)

    
    def listen_shell(self):    
        while True:
            message = self.shell.recvfrom(8192)[0]  
            print_message("Shell received \"" + message[:len(message)-1]+"\"")    
            self.handle_shell_request(message)

    
    def listen_all(self):
        print_message("Starting EasyBackup Peer Daemon with PID " + str(os.getpid()) + " ...")
        shell = Thread(target=self.listen_shell, args=())
        mc = Thread(target=self.listen, args=(self.mc,"MC"))
        mdb = Thread(target=self.listen, args=(self.mdb,"MDB"))
        mdr = Thread(target=self.listen, args=(self.mdr,"MDR"))
        shell.start()
        print_message("Shell listening at UDP port " + str(self.shell_port))
        mdb.start()  
        print_message("MDB listening at Multicast group "+ self.mdb_address + " and port " + str(self.mdb_port))     
        mc.start()
        print_message("MC listening at Multicast group "+ self.mc_address + " and port " + str(self.mc_port))
        mdr.start()
        print_message("MDR listening at Multicast group "+ self.mdr_address + " and port " + str(self.mdr_port))
        shell.join()
        mdb.join()
        mc.join()
        mdr.join()

    
    def create_multicast_socket(self,multicast_address,multicast_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((multicast_address, multicast_port))
        mreq = struct.pack("4sl", socket.inet_aton(multicast_address), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return sock
    
    def create_socket(self,port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        return  s
    
    def listen(self,sock,channel):
        while True:
            message,addr = sock.recvfrom(10240)
            operation=message.split(" ")[0]
            print_message(channel+" received " + operation + " from " + str(addr) )    
            request = Thread(target=self.handle_request, args=(message,))
            request.start()
            request.join()
            
    def handle_request(self, message):
        a=""
       
    def handle_shell_request(self, message):
        args=message.split(" ")
        operation=args[0]
        if(operation=="backup"):
            file_path=args[1]
            replication_degree=args[2]
            self.send_chunks(file_path,replication_degree)
            
        
    def send_chunks(self, path,replication_degree):
        f = File(path)
        f.generate_chunks(self.temp_dir)
        chunks=f.fetch_chunks(self.temp_dir)
        for j in range(len(chunks)):
            chunk_file = open(self.temp_dir +chunks[j], "rb")
            body=chunk_file.read()
            file_id=f.generate_file_id()
            replication_degree=str(replication_degree)
            chunk_no=str(j)
            message="PUTCHUNK " + VERSION + " " + file_id + " " + chunk_no + " " + replication_degree + CRLF + CRLF + body
            self.mdb.sendto(message, (self.mdb_address, self.mdb_port))