import sqlite3
from os.path import expanduser
class Data:
    def __init__(self, database):
        self.conection = sqlite3.connect(database)
        self.cursor = self.conection.cursor()
    
    def add_file(self, file_name, file_id, date_modified, chunk_no):
        db_file_id = self.get_file_id(file_name)
        if (db_file_id == -1):
            self.cursor.execute("insert into files values(?)", (file_name))
            self.cursor.commit()
            db_file_id = self.get_file_id(file_name)
 
        self.cursor.execute("insert into files_modified values (?, ?, ?, ?)", (file_id, db_file_id, date_modified, chunk_no))
        self.cursor.commit()
        self.cursor.close()
 
    
    def get_file_id (self, file_name):
        try:
            self.cursor.execute("select * from files where name = " + file_name)
            db_id = self.cursor.fetchone()['id']
            return db_id
        except:
            return -1
        
    def get_file_history(self, file_name):
        db_file_id = self.get_file_id(file_name)
        if (db_file_id != -1):
            self.cursor.execute("select * from files_modified where file = " + db_file_id)
            
    
    def delete_file_instance (self, file_name, date_modified):
        db_file_id = self.get_file_id(file_name)
        if (db_file_id == -1):
            return False
        else:
            self.cursor.execute("select * from files_modified where file = " + db_file_id + " and date_modified = " + date_modified)
            db_modified_id = self.cursor.fetchone()['id']
            self.cursor.execute("delete from files_modified where id = " + db_modified_id)
            self.cursor.commit()
            
    def delete_file (self, file_name):
        db_file_id = self.get_file_id(file_name)
        if (db_file_id != -1):
            self.cursor.execute("delete from files where id = " + db_file_id)
        return True
# Tests
#path = expanduser("~") + "/easybackup/data.db"
#c=sqlite3.connect(path.decode("latin1"))
c=Data("c:\git\easybackup\data.db")