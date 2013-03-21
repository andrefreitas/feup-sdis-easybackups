"""
This class describes a peer computer. The peer have a home directory
that is where the backups are store and the temporary files, ie. chunks
that were generated to send to another peer in the network.
"""
import os
import socket
import struct
import random
import time
import re
from file import File
from threading import Thread,Timer
from datetime import datetime


BACKUP_DIR="backup"
TEMP_DIR="temp"
SHELL_PORT=8383
VERSION="1.0"
CRLF="\n\r"
MAX_MESSAGE_SIZE=65565
TTL=1
MAX_ATTEMPTS=5
TIMEOUT=0.5
quit_waiting=False

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
            message = self.shell.recvfrom(MAX_MESSAGE_SIZE)[0]  
            print_message("Shell received \"" + message[:len(message)-1]+"\"")    
            self.handle_shell_request(message)
            
    def listen(self,sock,channel):
        while True:
            message,addr = sock.recvfrom(MAX_MESSAGE_SIZE)
            operation=message.split(" ")[0].strip(' \t\n\r')
            print_message(channel+" received \"" + operation + "\" from " + str(addr) )
            self.handle_request(message)

    
    def listen_all(self):
        pid=str(os.getpid())
        print_message("Starting EasyBackup Peer Daemon with PID " + pid + " ...")
        f=open(self.home_dir+"/pid.txt","w")
        f.write(pid)
        f.close()
        shell = Thread(target=self.listen_shell, args=())
        #mc = Thread(target=self.listen, args=(self.mc,"MC"))
        mdb = Thread(target=self.listen, args=(self.mdb,"MDB"))
        mdr = Thread(target=self.listen, args=(self.mdr,"MDR"))
        shell.start()
        print_message("Shell listening at UDP port " + str(self.shell_port))
        mdb.start()  
        print_message("MDB listening at Multicast group "+ self.mdb_address + " and port " + str(self.mdb_port))     
        #mc.start()
        print_message("MC listening at Multicast group "+ self.mc_address + " and port " + str(self.mc_port))
        mdr.start()
        print_message("MDR listening at Multicast group "+ self.mdr_address + " and port " + str(self.mdr_port))
        shell.join()
        mdb.join()
        #mc.join()
        mdr.join()

    
    def create_multicast_socket(self,multicast_address,multicast_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", multicast_port))
        mreq = struct.pack("4sl", socket.inet_aton(multicast_address), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, TTL)
        sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)
        return sock
    
    def create_socket(self,port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        return  s
    
    def handle_request(self, message):
        operation=message.split(" ")[0].strip(' \t\n\r')
        if (operation == "PUTCHUNK"):
            self.backup_chunk(message)
       
    def backup_chunk(self, message):
        message_list=message.split(" ")
        fileid=message_list[2]
        chunkno=message_list[3]
        chunk = message.split(CRLF+CRLF)[1]
        chunk_file = open(self.backup_dir+fileid+"_"+chunkno+".chunk", "wb")
        chunk_file.write(chunk)
        chunk_file.close()
        delay=random.randint(0,400)/1000.0
        time.sleep(delay)
        message="STORED " + VERSION +  " " +  fileid + " " + chunkno +CRLF+CRLF
        self.mc.sendto(message, (self.mc_address, self.mc_port))
        
        
    def handle_shell_request(self, message):
        args=message.split(" ")
        operation=args[0]
        if(operation=="backup"):
            file_path=args[1]
            replication_degree=args[2]
            if(self.send_chunks(file_path,int(replication_degree))):
                self.shell.sendto("ok\n", ("127.0.0.1", self.shell_port))
            else:
                self.shell.sendto("fail\n", ("127.0.0.1", self.shell_port))
            
        
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
            acks=False
            attempts=0
            timeout=TIMEOUT
            while(not acks and attempts<MAX_ATTEMPTS):   
                self.mdb.sendto(message, (self.mdb_address, self.mdb_port))
                if(self.check_replication_degree(file_id,chunk_no,replication_degree,timeout)):
                    acks=True
                timeout*=2
                attempts+=1
            return acks
                
    
    def check_replication_degree(self, file_id, chunk_no, replication_degree,timeout):
        replication_degree=int(replication_degree)
        global quit_waiting
        acks=0
        timeout_check = Timer(timeout, self.quit_waiting)
        quit_waiting=False
        timeout_check.start()
        while (acks < replication_degree and not quit_waiting):
            message=None
            try:
                self.mc.settimeout(timeout)
                message = self.mc.recv(MAX_MESSAGE_SIZE)
                message_expected="^STORED " + VERSION +  " " +  file_id + " " + chunk_no
                if (re.search(message_expected,message)):
                    acks += 1
            except:
                pass
            self.mc.setblocking(1)
        
        if(quit_waiting and acks < replication_degree):
            print_message("Timeout getting the desired replication degree")
        return acks==replication_degree     
    
    def quit_waiting(self):
        global quit_waiting
        quit_waiting = True
            
    