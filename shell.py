import socket
import re
import os
from peer import MAX_MESSAGE_SIZE

class Shell:
    def __init__(self, port=8383):
        self.hostname = "127.0.0.1"
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def send_message(self, message):
        self.socket.sendto(message, (self.hostname, self.port))
        
    def receive_message(self):
        answer = self.socket.recv(MAX_MESSAGE_SIZE)
        return answer
    
    def backup_file(self, full_path, replication_degree=2):
        directory=self.assure_full_path(full_path)
        self.send_message("backup "+directory+full_path+" "+str(replication_degree)+"\n")
        print self.receive_message()
    
    def restore_file(self,full_path):
        directory=self.assure_full_path(full_path)
        self.send_message("restore "+directory+full_path+"\n")
        print self.receive_message()
        
    def assure_full_path(self,full_path):
        file_extension_pattern="^[a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+$"
        directory=""
        if (re.match(file_extension_pattern, full_path)):
            directory = os.getcwd()+"/"
        return directory
        
   
        
    

    
    
    
        