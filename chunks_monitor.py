from data import Data
import peer
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re

class ChunksMonitor(FileSystemEventHandler):
    
    def __init__(self,backup_directory,socket,address,port,db_path):
        self.backup_directory=backup_directory
        self.db=Data(db_path)
        self.socket=socket
        self.address=address
        self.port=port
        
    def on_any_event(self,event):
        event=re.split("/|\\\\",str(event))
        chunk=event[-1].strip(">")
        peer.print_message("The chunk "+ chunk +" has been deleted/moved")
        self.socket.sendto("REMOVED",(self.address,self.port))
        
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