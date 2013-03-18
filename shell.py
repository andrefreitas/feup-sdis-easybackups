import socket
import re
import os

class Shell:
    def __init__(self, port=8383):
        self.hostname = "127.0.0.1"
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def send_message(self, message):
        self.socket.sendto(message, (self.hostname, self.port))
        
    def receive_message(self, message):
        answer,addr= self.socket.recvfrom(10240)
        return answer
    
    def backup_file(self, full_path, replication_degree=2):
        file_extension_pattern="^[a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+$"
        directory=""
        if (re.match(file_extension_pattern, full_path)):
            directory = os.getcwd()+"/"
        self.send_message("backup "+directory+full_path+" "+str(replication_degree)+"\n")
    
    
    
        