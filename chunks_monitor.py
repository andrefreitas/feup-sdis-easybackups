from data import Data
import peer
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re

class ChunksMonitor(FileSystemEventHandler):
    
    def __init__(self,backup_directory,socket,address,port,db_path):
        self.backup_directory=backup_directory
        self.db_path=db_path
        self.socket=socket
        self.address=address
        self.port=port
        
    def send_removed(self,event,action):
        data=Data(self.db_path)
        event=re.split("/|\\\\",str(event))
        chunk=event[-1].strip(">")
        file_name=chunk
        if(re.search("_",chunk)):
            peer.print_message("The chunk "+ chunk +" has been "+action)
            chunk=chunk.split(".")[0]
            chunk=chunk.split("_")
            file_id=chunk[0]
            chunk_number=chunk[1]
            if(data.chunk_sha256_exist(chunk_number, file_id)):
                message="REMOVED "+peer.VERSION+" "+file_id+" "+chunk_number+peer.CRLF+peer.CRLF
                peer.print_message("The chunk "+ file_name +" has been "+action)
                self.socket.sendto(message,(self.address,self.port))
    
    def on_moved(self, event):
        self.send_removed(event,"moved")
        
    def on_deleted(self, event):
        self.send_removed(event,"deleted")

        
    def start(self):
        event_handler = self
        observer = Observer()
        observer.schedule(event_handler, self.backup_directory, recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()