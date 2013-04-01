"""
 Shell
 Authors: Ana Gomes, Andre Freitas
 Description: This is a class that is used by the EasyBackup Shell and does all the work,
 sending requests to the peer daemon.
"""
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
        answer=self.receive_message().strip(" \n")
        if(answer=="ok"):
            print "Backup done successfully!"
        else:
            print "Backup failed. Try another replication degree?"
    
    def restore_file(self,full_path):
        directory=self.assure_full_path(full_path)
        self.send_message("restore "+directory+full_path+"\n")
        answer = self.receive_message().split(" ")
        if (answer[1]):
            i=0
            print "\nFound " + answer[1] + " modifications. Please choose one of the following: \n" 
            for modification_date in answer[2:]:
                i+=1
                print str(i)+ " - " + modification_date
            while True:
                option = int(raw_input("\n> "))
                if (option >= 1 and option <= int(answer[1])):
                    self.send_message("restoremodification " + directory + full_path + " " +str(option) )
                    print "Check your ~/easybackup/restore directory"
                    break
        else:
            print "No modifications found."
            
    def delete_file(self,full_path):
        directory=self.assure_full_path(full_path)
        self.send_message("delete "+directory+full_path)
        
    def delete2_file(self,full_path):
        directory=self.assure_full_path(full_path)
        self.send_message("delete2 "+directory+full_path)
        
        
    def assure_full_path(self,full_path):
        file_extension_pattern="^[a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+$"
        directory=""
        if (re.match(file_extension_pattern, full_path)):
            directory = os.getcwd()+"/"
        return directory
        
   
        
    

    
    
    
        