import sqlite3

class Data:
    def __init__(self, database):
        self.conection = sqlite3.connect(database)
        self.cursor = self.conection.cursor()
    
    def query(self,query):
        self.cursor.execute(query)
        self.conection.commit()
        return self.cursor.fetchall()
        
    def add_file(self, name):
        try:
            self.query("INSERT INTO files(name) VALUES (\""+name+"\")")
            return True
        except:
            return False
    
    def get_file_id(self,name):
        result=self.query("SELECT * FROM files WHERE name=\""+name+"\"")
        return result[0][0] if(len(result)) else False
        
    def add_modification(self,file_name,sha256,chunks,date):
        if (not self.get_modification_id(sha256)):
            file_id=self.get_file_id(file_name)
            if(not file_id): return False
            sql="INSERT INTO modifications(sha256,file_id,chunks,date_modified)"
            sql+="VALUES (\""+sha256+"\","+ str(file_id) + "," + str(chunks) + ",\""+date+"\")"
            self.query(sql)
            return True
        return True
    
    def get_modification_id(self,sha256):
        result=self.query("SELECT * FROM modifications WHERE sha256=\""+sha256+"\"")
        return result[0][0] if(len(result)) else False
        
    def add_chunk(self,modification_sha256,number,replication_degree):
        modification_id=self.get_modification_id(modification_sha256)
        if(not modification_id): return False
        if(not self.chunk_exist(number, replication_degree, modification_id)):            
            sql="INSERT INTO chunks(number,replication_degree,modification_id)"
            sql+="VALUES ("+str(number)+","+str(replication_degree)+","+str(modification_id)+")"
            self.query(sql)
        return True
    
    def chunk_exist(self, number, replication_degree, modification_id):
        sql = "SELECT * from chunks where number = " + str(number) + " and replication_degree = " + str(replication_degree) + " and modification_id = " + str(modification_id)
        return len(self.query(sql))>0      
    
    def get_file_modifications(self,file_name):
        file_id=self.get_file_id(file_name)
        if(not file_id): return []
        return self.query("SELECT * FROM modifications WHERE file_id="+str(file_id))
        
    def get_modification_chunks(self,modification_sha256):
        modification_id=self.get_modification_id(modification_sha256) 
        if(not modification_id): return False
        return self.query("SELECT * FROM chunks WHERE modification_id="+str(modification_id))
    
    def get_modifications(self):
        return self.query("SELECT * FROM modifications")
    
    def get_files(self):
        return self.query("SELECT * FROM files")
    
    def get_chunks(self):
        return self.query("SELECT * FROM chunks")
    
   
    
# Tests
#path = expanduser("~") + "/easybackup/data.db"
#c=sqlite3.connect(path.decode("latin1"))
#conn=sqlite3.connect("c:\git\easybackup\data.db")
#c = conn.cursor()
# c=Data("c:\git\easybackup\data.db")