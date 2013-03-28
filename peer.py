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
import shutil
from file import File
from threading import Thread,Timer
from datetime import datetime
from datetime import timedelta
from data import Data
from chunks_monitor import ChunksMonitor


BACKUP_DIR="backup"
TEMP_DIR="temp"
RESTORE_DIR="restore"
SHELL_PORT=8383
VERSION="1.0"
CRLF="\n\r"
MAX_MESSAGE_SIZE=65565
TTL=1
MAX_ATTEMPTS=5
TIMEOUT=0.5
LOOPBACK=0
waiting=False
stop_restore_waiting=False
subscriptions={}
restored={}

def print_message(message):
    print  "[" + datetime.now().strftime("%d/%m/%y %H:%M") + "] " + message

class Peer:
    def __init__(self, home_dir,mc_address,mc_port,mdb_address,mdb_port,mdr_address,mdr_port,backup_size,shell_port=SHELL_PORT):
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
        self.db_path = self.home_dir + "/data.db"
        self.db_path = self.db_path.decode("latin1")
        self.can_send_removed=True
        self.reject_putchunks={}
        self.backup_size = backup_size
        self.needs_space_reclaiming()
        
    def needs_space_reclaiming(self):
        if (self.backup_size < self.check_directory_size(self.backup_dir)):
            self.remove_chunks_higher_replication_degree()
            return True
        return False
    
    def remove_chunks_higher_replication_degree(self):
        data = Data(self.db_path)
        chunks = data.get_ordered_chunks_difference_replication_degree()
        el = 0
        while (self.backup_size < self.check_directory_size(self.backup_dir)):
            modification_id = chunks[el][4]
            chunk_number = chunks[el][1]
            sha256 = data.get_chunk_sha256(modification_id)
            data.delete_chunk_removed(chunk_number, sha256)
            file_name = self.backup_dir+str(sha256)+"_"+str(chunk_number)+".chunk"
            os.remove(file_name)
            message = "REMOVED " + VERSION + " " + sha256 + " " + str(chunk_number)
            self.shell.sendto(message, ("127.0.0.1", self.shell_port))
            el +=1
            
    def init_home_dir(self):
        self.backup_dir=self.home_dir+"/"+BACKUP_DIR+"/"
        if(not os.path.exists(self.backup_dir)):
            os.makedirs(self.backup_dir)
            
        self.temp_dir=self.home_dir+"/"+TEMP_DIR+"/"
        if(not os.path.exists(self.temp_dir)):
            os.makedirs(self.temp_dir)
            
        self.restore_dir=self.home_dir+"/"+RESTORE_DIR+"/"
        if(not os.path.exists(self.restore_dir)):
            os.makedirs(self.restore_dir)
               
        if(not os.path.exists(self.home_dir+"/data.db")):
            shutil.copy2("data.db", self.home_dir)
        
    
    def listen_shell(self):    
        while True:
            message,addr = self.shell.recvfrom(MAX_MESSAGE_SIZE)
            message=message.strip(' \t\n\r')
            print_message("Shell received \"" + message+"\"")
            self.handle_shell_request(message,addr)

    def listen(self,sock,channel):
        while True:
            global subscriptions
            message,addr = sock.recvfrom(MAX_MESSAGE_SIZE)
            if message in subscriptions:
                value = subscriptions[message]
                subscriptions[message] = int(value)+1
            operation=message.split(" ")[0].strip(' \t\n\r')
            print_message(channel+" received \"" + operation + "\" from " + str(addr) )
            self.handle_request(message,addr)

    
    def listen_all(self):
        pid=str(os.getpid())
        print_message("Starting EasyBackup Peer Daemon with PID " + pid + " ...")
        f=open(self.home_dir+"/pid.txt","w")
        f.write(pid)
        f.close()
        shell = Thread(target=self.listen_shell, args=())
        mc = Thread(target=self.listen, args=(self.mc,"MC"))
        mdb = Thread(target=self.listen, args=(self.mdb,"MDB"))
        mdr = Thread(target=self.listen, args=(self.mdr,"MDR"))
        monitor_chunks=Thread(target=self.monitor_chunks, args=())
        shell.start()
        print_message("Shell listening at UDP port " + str(self.shell_port))
        mdb.start()  
        print_message("MDB listening at Multicast group "+ self.mdb_address + " and port " + str(self.mdb_port))     
        mc.start()
        print_message("MC listening at Multicast group "+ self.mc_address + " and port " + str(self.mc_port))
        mdr.start()
        print_message("MDR listening at Multicast group "+ self.mdr_address + " and port " + str(self.mdr_port))
        monitor_chunks.start()
        shell.join()
        mdb.join()
        mc.join()
        mdr.join()
        monitor_chunks.join()
        
    
    def monitor_chunks(self):
        monitor=ChunksMonitor(self.backup_dir, self.shell_port,self.db_path)
        monitor.start()
        monitor.join()
        
    
    def create_multicast_socket(self,multicast_address,multicast_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", multicast_port))
        mreq = struct.pack("4sl", socket.inet_aton(multicast_address), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, TTL)
        sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, LOOPBACK)
        return sock
    
    def create_socket(self,port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        return  s
    
    def handle_shell_request(self, message,addr):
        args=message.split(" ")
        operation=args[0]
        data = Data(self.db_path)
        if(operation=="backup"):
            file_path=args[1]
            replication_degree=args[2]
            if(self.send_chunks(file_path,int(replication_degree))):
                self.shell.sendto("ok\n", addr)
            else:
                self.shell.sendto("fail\n", addr)
        elif(operation=="restore"):
            file_path=args[1]
            modifications=data.get_file_modifications(file_path)
            message="found "+ str(len(modifications))
            for modification in modifications:
                modification_date=modification[2]
                modification_date=modification_date[:10]+"T"+modification_date[11:19]
                message+= " " + modification_date
            self.shell.sendto(message,addr)
        
        elif(operation=="restoremodification"):
            file_name = args[1]
            option = int(args[2])
            modification = data.get_file_modifications(file_name)[option-1]
            sha256 = modification[1]
            chunks = int(modification[3])
            self.restore_file_modification(sha256, chunks)
            self.get_file(sha256, file_name,chunks)
            
        elif(operation=="delete"):
            file_name=args[1]
            self.request_file_deletion(file_name)
            
        elif(operation=="REMOVED"):
            if(self.can_send_removed):
                file_id=message.split(" ")[2]
                chunk_number=message.split(" ")[3]
                self.reject_putchunks[file_id+chunk_number]=datetime.now() + timedelta(0,60)
                message+=CRLF+CRLF
                self.mc.sendto(message,(self.mc_address,self.mc_port))
    
    def handle_request(self, message,addr):
        operation=message.split(" ")[0].strip(' \t\n\r')
        message=message.strip(' \t\n\r')
        if (operation == "PUTCHUNK"):
            data = Data(self.db_path)
            file_id=message.split(" ")[2]
            chunk_number=message.split(" ")[3]
            now=datetime.now()
            body = message.split(CRLF+CRLF)[1]
            can_store=True
            if(data.chunk_owner(file_id)):
                can_store=False
            if((file_id+chunk_number) in self.reject_putchunks and now<self.reject_putchunks[file_id+chunk_number]):
                can_store=False
            if ((self.backup_size - self.check_directory_size(self.backup_dir)) <= len(body)):
                can_store=False 
            if(can_store):
                self.backup_chunk(message)
            else: 
                print_message("PUTCHUNK rejeitado")
                
        elif(operation == "GETCHUNK"):
            self.get_and_send_chunk(message)
        elif(operation == "CHUNK"):
            self.save_chunk_to_restore(message)
        elif(operation=="DELETE"):
            self.can_send_removed=False
            self.delete_chunks(message)
            time.sleep(1)
            self.can_send_removed=True
        elif(operation=="STORED"):
            self.increment_chunk_replication_degree(message,addr)
        elif(operation=="REMOVED"):
            self.update_chunk_replication_degree(message,addr)
            
    def update_chunk_replication_degree(self,message,addr):
        file_id=message.split(" ")[2]
        chunk_number=message.split(" ")[3].strip(CRLF+CRLF)
        host=addr[0]
        data = Data(self.db_path)
        if(data.get_chunk_id(chunk_number, file_id)):
            data.remove_chunk_replication_degree(file_id, chunk_number, host)
            # check replication degree
            replication_degree=data.get_chunk_replication_degree(file_id, chunk_number)
            minimum_replication_degree=data.get_chunk_minimum_replication_degree(file_id , chunk_number)
            if(replication_degree<minimum_replication_degree):
                self.put_chunk(file_id,chunk_number,replication_degree)
            
            
    def increment_chunk_replication_degree(self,message,addr):
        ip=addr[0]
        data = Data(self.db_path)
        file_id=message.split(" ")[2]
        chunk_number=message.split(" ")[3]
        print "file_id: *"+file_id+"*"
        print "chunk_number: *"+chunk_number+"*"
        if(data.increment_replication_degree(file_id, chunk_number,ip)):
            print "replication degree: " + str(data.get_chunk_replication_degree(file_id, chunk_number))
              
    def create_chunk_data(self,message):
        data = Data(self.db_path)
        file_id=message.split(" ")[2]
        chunk_number=message.split(" ")[3]
        minimum_replication_degree=message.split(" ")[4].split(CRLF+CRLF)[0]
        data.add_only_modification(file_id)
        data.add_chunk(file_id, chunk_number, minimum_replication_degree)
        data.increment_replication_degree(file_id, chunk_number,"localhost")
    
    def backup_chunk(self, message):
        message_list=message.split(" ")
        file_id=message_list[2]
        chunk_no=message_list[3]
        chunk = message.split(CRLF+CRLF)[1]
        chunk_file = open(self.backup_dir+file_id+"_"+chunk_no+".chunk", "wb")
        chunk_file.write(chunk)
        chunk_file.close()
        self.create_chunk_data(message)
        delay=random.randint(0,400)
        d = delay/1000.0
        time.sleep(d)
        message="STORED " + VERSION +  " " +  file_id + " " + chunk_no + CRLF + CRLF
        self.mc.sendto(message, (self.mc_address, self.mc_port))

        
    def get_file(self, sha256, file_name,chunks):
        f = File(file_name,sha256)
        while(not f.restore_file(self.temp_dir, self.restore_dir,chunks)):
            pass
        self.remove_chunks_from_directory(f.get_file_id(), self.temp_dir)
        return True
        
    def request_file_deletion(self, file_name):
        data = Data(self.db_path)
        modifications=data.get_file_modifications(file_name)
        for modification in modifications:
            file_id=modification[1]
            message="DELETE "+str(file_id)+CRLF+CRLF
            self.mc.sendto(message, (self.mc_address, self.mc_port))
            
    def delete_chunks(self,message):
        file_id=message.split(" ")[1].strip(CRLF+CRLF)
        self.remove_chunks_from_directory(file_id, self.backup_dir) 
        
        
    def restore_file_modification(self, file_id, chunks):
        total_chunks=0
        for i in range(chunks):
            message = "GETCHUNK " + VERSION + " " + file_id + " " + str(i) + CRLF + CRLF
            message_expected = "CHUNK " + VERSION + " " + file_id + " " + str(i)
            restored[message_expected] = False
            chunk_received = False
            attempts=0
            timeout = TIMEOUT
            while (not chunk_received and attempts < MAX_ATTEMPTS):
                self.mc.sendto(message, (self.mc_address, self.mc_port))
                if (self.check_received_chunk(message_expected, timeout)):
                    chunk_received = True
                    total_chunks+=1
                else:
                    timeout*=2
                    attempts+=1
            
        return total_chunks == chunks

    def check_received_chunk(self, message_expected, timeout):
        global stop_restore_waiting
        chunk_received=False
        timeout_check = Timer(timeout, self.restore_waiting)
        timeout_check.start()
        while (not chunk_received and not stop_restore_waiting):
            chunk_received = restored[message_expected]
        
        timeout_check.cancel()
        if (not chunk_received):
                print "Timeout while getting chunk."
        else:
            del restored[message_expected]
        
        return chunk_received      
        
    def restore_waiting(self):
        global stop_restore_waiting
        stop_restore_waiting = True

    def save_chunk_to_restore(self, message):
        original_message = message
        check_message = message.split(CRLF+CRLF)[0]
        if (check_message in restored):
            restored[check_message] = True
            message = message.split(" ")
            file_id = message[2]
            splited = original_message.split(CRLF+CRLF)
            chunk_no = splited[0].split(" ")[3]
            body = splited[1]
            chunk = open(self.temp_dir+file_id+"_"+chunk_no+".chunk", "wb")
            chunk.write(body)
            chunk.close()
            
    def put_chunk(self,file_id,chunk_number,replication_degree):
        full_path = self.backup_dir+file_id+"_"+chunk_number+".chunk"
        if (os.path.exists(full_path)):
            chunk = open(full_path, "rb")
            chunk_content = chunk.read()
            chunk.close()
            message="PUTCHUNK " + VERSION + " " + str(file_id) + " " + str(chunk_number)+" "+str(replication_degree) + CRLF + CRLF + chunk_content
            delay=random.randint(0,400)/1000.0
            time.sleep(delay)
            self.mdr.sendto(message, (self.mdr_address, self.mdr_port))

    def get_and_send_chunk(self, message):
        message_list=message.split(" ")
        file_id=message_list[2]
        chunk_no=message_list[3]
        full_path = self.backup_dir+file_id+"_"+chunk_no+".chunk"
        if (os.path.exists(full_path)):
            chunk = open(full_path, "rb")
            chunk_content = chunk.read()
            chunk.close()
            message="CHUNK " + VERSION + " " + file_id + " " + chunk_no + CRLF + CRLF + chunk_content
            delay=random.randint(0,400)/1000.0
            time.sleep(delay)
            self.mdr.sendto(message, (self.mdr_address, self.mdr_port))

    def send_chunks(self, path,replication_degree):
        f = File(path)
        data = Data(self.db_path)
        if (not data.get_file_id(path)):
            data.add_file(path)
        chunks_number = f.generate_chunks(self.temp_dir)
        file_id=f.generate_file_id()
        date = f.get_modification_date()
        data.add_modification(path, file_id, chunks_number, date)
        chunks=f.fetch_chunks(self.temp_dir)
        acks_chunks=0
        for j in range(len(chunks)):
            chunk_file = open(self.temp_dir +chunks[j], "rb")
            body=chunk_file.read()
            chunk_file.close()
            replication_degree=str(replication_degree)
            chunk_no=str(j)
            message="PUTCHUNK " + VERSION + " " + file_id + " " + chunk_no + " " + replication_degree + CRLF + CRLF + body
            acks=False
            attempts=0
            timeout=TIMEOUT
            while(not acks and attempts<MAX_ATTEMPTS):
                self.mdb.sendto(message, (self.mdb_address, self.mdb_port))
                data.add_chunk(file_id, chunk_no, replication_degree)
                if(self.check_replication_degree(file_id,chunk_no,replication_degree,timeout)):
                    acks=True
                timeout*=2
                attempts+=1
            if(acks): acks_chunks+=1
        self.remove_chunks_from_directory(f.get_name(),self.temp_dir)
        return (acks_chunks>=chunks_number)
                
    
    def check_replication_degree(self, file_id, chunk_no, replication_degree,timeout):
        replication_degree=int(replication_degree)
        acks=0
        global waiting
        waiting=False
        timeout_check = Timer(timeout, self.quit_waiting)
        timeout_check.start()
        message_expected="STORED " + VERSION +  " " +  file_id + " " + chunk_no + CRLF + CRLF
        global subscriptions
        subscriptions[message_expected] = 0
        while (acks < replication_degree and not waiting):
            acks = subscriptions[message_expected]
        
        if(waiting and acks < replication_degree):
            print_message("Timeout getting the desired replication degree")
        
        timeout_check.cancel()
        return acks==replication_degree     
    
    def quit_waiting(self):
        global waiting
        waiting = True
        
    def remove_chunks_from_directory(self,file_id,directory):
        file_id = file_id.split(".")[0]
        list_dir = os.listdir(directory)
        for file_name in list_dir:
            match = re.search(file_id, file_name)
            if (match):
                os.remove(directory+file_name)
    
    # Formato retornado em Bytes       
    def check_directory_size(self, directory):
        TotalSize = 0
        for item in os.walk(directory):
            for file_name in item[2]:
                try:
                    TotalSize = TotalSize + os.path.getsize(os.path.join(item[0], file_name))
                except:
                    print("error with file:  " + os.path.join(item[0], file_name))
        return TotalSize 
    