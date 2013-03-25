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
    
    def add_only_modification(self,sha256):
        if (not self.get_modification_id(sha256)):
            sql="INSERT INTO modifications(sha256)"
            sql+="VALUES (\""+sha256+"\")"
            self.query(sql)
        return True
    
    def get_modification_id(self,sha256):
        result=self.query("SELECT * FROM modifications WHERE sha256=\""+sha256+"\"")
        return result[0][0] if(len(result)) else False
        
    def add_chunk(self,modification_sha256,number,minimum_replication_degree):
        modification_id=self.get_modification_id(modification_sha256)
        if(not modification_id): return False
        if(not self.chunk_exist(number, modification_id)):            
            sql="INSERT INTO chunks(number,minimum_replication_degree,modification_id)"
            sql+="VALUES ("+str(number)+","+str(minimum_replication_degree)+","+str(modification_id)+")"
            self.query(sql)
        return True
    
    def chunk_exist(self, number, modification_id):
        sql = "SELECT * from chunks where number = " + str(number) + " and modification_id = " + str(modification_id)
        return len(self.query(sql))>0
    
    def increment_replication_degree(self,sha256,chunk_number,value): 
        modification_id=self.get_modification_id(sha256)
        print "id:" +str(modification_id)
        if(modification_id):
            old_replication_degree=self.query("SELECT replication_degree FROM chunks WHERE modification_id="+str(modification_id)+" and number="+str(chunk_number))
            if(len(old_replication_degree)==0):
                return False
            old_replication_degree=old_replication_degree[0][0]
            print "old: " +  str(old_replication_degree)
            new_replication_degree=old_replication_degree+value
            sql="UPDATE chunks"
            sql+=" SET replication_degree="+str(new_replication_degree)
            sql+=" WHERE modification_id="+str(modification_id)+" and number="+str(chunk_number)
            self.query(sql)
            return True
        else:
            return False  
        
    def reset_replication_degree(self,sha256,chunk_number):
        modification_id=self.get_modification_id(sha256)
        if(modification_id and self.chunk_exist(chunk_number,modification_id)):
            sql="UPDATE chunks"
            sql+=" SET replication_degree=0"
            sql+=" WHERE modification_id="+str(modification_id)+" and number="+str(chunk_number)
            self.query(sql)
        
    def get_chunk_replication_degree(self,sha256,chunk_number):
        modification_id=self.get_modification_id(sha256)
        result=self.query("SELECT * FROM chunks WHERE modification_id="+str(modification_id)+" and number="+str(chunk_number))
        return result[0][2]
    
    def get_chunk_minimum_replication_degree(self,sha256,chunk_number):
        modification_id=self.get_modification_id(sha256)
        result=self.query("SELECT * FROM chunks WHERE modification_id="+str(modification_id)+" and number="+str(chunk_number))
        return result[0][3]
    
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
#c=Data("c:\git\easybackup\data.db")
#c=Data("/home/andre/easybackup/data.db")