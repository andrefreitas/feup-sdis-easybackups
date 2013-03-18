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
import time
from threading import Thread

BACKUP_DIR="backup"
TEMP_DIR="temp"

class Peer:
    def __init__(self, home_dir,mc,mc_port,mdb,mdb_port,mdr,mdr_port):
        self.home_dir=home_dir
        self.init_home_dir()
        self.mc=mc
        self.mc_port=mc_port
        self.mdb=mdb
        self.mdb_port=mdb_port
        self.mdr=mdr
        self.mdr_port=mdr_port
        
        
    def init_home_dir(self):
        backup_path=self.home_dir+"/"+BACKUP_DIR
        if(not os.path.exists(backup_path)):
            os.makedirs(backup_path)
            
        temp_path=self.home_dir+"/"+TEMP_DIR
        if(not os.path.exists(temp_path)):
            os.makedirs(temp_path)    
        
    def listen_all(self):
        mc = Thread(target=self.listen, args=(self.mc,self.mc_port))
        mdb = Thread(target=self.listen, args=(self.mdb,self.mdb_port))
        mdr = Thread(target=self.listen, args=(self.mdr,self.mdr_port))
        mdb.start()       
        mc.start()
        mdr.start()
        mdb.join()
        mc.join()
        mdr.join()
      
        
        
    def listen(self,multicast_address,multicast_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', multicast_port))
        mreq = struct.pack("4sl", socket.inet_aton(multicast_address), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        while True:
            print sock.recv(10240)
            #self.send_chunk("D:\eclipse\wallpaper.jpg", sock)
       
    
    def send_chunk(self, path, socket):
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
            socket.sendall(chunk_file.read())
            
    
        
p=Peer("/home/andre/easybackup", "224.1.1.1", 5678, "224.1.1.2", 5778, "224.1.1.3", 5878)
p.listen_all()