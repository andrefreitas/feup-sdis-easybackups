"""
 Data
 Authors: Ana Gomes, Andre Freitas
 Description: This is a class to abstract the acess to the database by functions
"""
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
    
    def delete_chunk_removed(self, chunk_number, sha256):
        chunk_id = self.get_chunk_id(chunk_number, sha256)
        if(chunk_id):
            sql="DELETE FROM chunks WHERE id="+str(chunk_id)
            self.query(sql)
            return True
        return False
    
    def chunk_exist(self, number, modification_id):
        sql = "SELECT * from chunks where number = " + str(number) + " and modification_id = " + str(modification_id)
        return len(self.query(sql))>0
    
    def chunk_sha256_exist(self,number,sha256):
        modification_id=self.get_modification_id(sha256)
        if(modification_id):
            return self.chunk_exist(number,modification_id)
        else:
            return False
    
    def get_chunk_id(self,number, sha256):
        modification_id=self.get_modification_id(sha256)
        if(modification_id):
            result=self.query("SELECT id FROM chunks WHERE number="+str(number)+" AND modification_id="+str(modification_id))
            return result[0][0] if(len(result)>0) else False
        else:
            return False
      
    def chunk_host_exists(self,chunk_id,host_id):
        res=self.query("SELECT * FROM chunks_hosts WHERE chunk_id="+str(chunk_id)+" AND host_id="+str(host_id))  
        return len(res)>0
    
    def chunk_owner(self,sha256):
        modification_id=self.get_modification_id(sha256)
        if(not modification_id): return False
        return len(self.query("SELECT * FROM files, modifications WHERE files.id=modifications.file_id and modifications.id="+str(modification_id))) > 0
        
        
    def increment_replication_degree(self,sha256,chunk_number,host): 
        modification_id=self.get_modification_id(sha256)
        chunk_id=self.get_chunk_id(chunk_number,sha256)
        self.add_host(host) 
        host_id=self.get_host_id(host)
        if(modification_id and chunk_id and host_id):
            if(not self.chunk_host_exists(chunk_id,host_id)):
                self.query("INSERT INTO chunks_hosts(chunk_id,host_id) VALUES("+str(chunk_id)+","+str(host_id)+")")
                replication_degree = self.get_chunk_replication_degree(sha256, chunk_number)
                self.cursor.execute("UPDATE chunks SET replication_degree=? WHERE id = ?" ,( str(replication_degree), str(chunk_id)))
                self.conection.commit()
            return True
        else:
            return False  
        
    def get_chunk_replication_degree(self,sha256,chunk_number):
        chunk_id=self.get_chunk_id(chunk_number, sha256)
        if(chunk_id):
            result=self.query("SELECT COUNT(*) FROM chunks_hosts WHERE chunk_id="+str(chunk_id))
            return result[0][0]
        else:
            return False
        
    def chunk_have_replication_host(self,sha256,chunk_number,host):
        modification_id=self.get_modification_id(sha256)
        chunk_id=self.get_chunk_id(chunk_number,sha256)
        host_id=self.get_host_id(host)
        if(modification_id and chunk_id and host_id):
            res=self.query("SELECT * FROM chunks_hosts WHERE chunk_id="+str(chunk_id)+" AND host_id="+str(host_id))
            return len(res)>0
        return False
            
        
    def remove_chunk_replication_degree(self,sha256,chunk_number,host):
        modification_id=self.get_modification_id(sha256)
        chunk_id=self.get_chunk_id(chunk_number,sha256)
        host_id=self.get_host_id(host)
        if(modification_id and chunk_id and host_id):
            self.query("DELETE FROM chunks_hosts WHERE chunk_id="+str(chunk_id)+" AND host_id="+str(host_id))
            replication_degree = self.get_chunk_replication_degree(sha256, chunk_number)
            self.cursor.execute("UPDATE chunks SET replication_degree=? WHERE id = ?" ,( str(replication_degree), str(chunk_id)))
            self.conection.commit()
            return True
        return False
        
    def get_chunk_minimum_replication_degree(self,sha256,chunk_number):
        modification_id=self.get_modification_id(sha256)
        if(modification_id):
            result=self.query("SELECT * FROM chunks WHERE modification_id="+str(modification_id)+" and number="+str(chunk_number))
            return result[0][3] if len(result)>0 else False
        return False

    def get_ordered_chunks_difference_replication_degree(self):
        sql="SELECT * FROM chunks ORDER BY replication_degree - minimum_replication_degree DESC"
        return self.query(sql)
    
    def get_chunk_sha256(self, modification_id):
        sql="SELECT * FROM modifications WHERE id="+str(modification_id)
        return self.query(sql)[0][1]
    
    def get_chunk_hosts(self,sha256,chunk_number):
        chunk_id=self.get_chunk_id(chunk_number, sha256)
        if(chunk_id):
            sql="SELECT hosts.host FROM chunks_hosts, hosts WHERE chunks_hosts.chunk_id="+str(chunk_id)+" AND chunks_hosts.host_id=hosts.id"
            return self.query(sql)
        else:
            return False
            
       
    def get_file_modifications(self,file_name):
        file_id=self.get_file_id(file_name)
        if(not file_id): return []
        return self.query("SELECT * FROM modifications WHERE file_id="+str(file_id))
        
    def get_modification_chunks(self,modification_sha256):
        modification_id=self.get_modification_id(modification_sha256) 
        if(not modification_id): return False
        return self.query("SELECT * FROM chunks WHERE modification_id="+str(modification_id))
    
    def host_exists(self,host):
        return len(self.query("SELECT * FROM hosts WHERE host=\""+host+"\""))>0
    
    def add_host(self,host):
        if(not self.host_exists(host)):         
            self.query("INSERT INTO hosts(host) VALUES(\""+host+"\")")
        return True
    
    def get_host_id(self,host):
        if(self.host_exists(host)):
            return self.query("SELECT id FROM hosts WHERE host=\""+host+"\"")[0][0]
        else:
            return False
        
    def get_host(self, host_id):
        return self.query("SELECT host FROM hosts WHERE id="+str(host_id))[0][0]
        
    def get_hosts_associated_chunk(self, chunk_id):
        return self.query("SELECT * FROM chunks_hosts WHERE chunk_id=" + str(chunk_id))
    
    def get_modifications(self):
        return self.query("SELECT * FROM modifications")
    
    def get_files(self):
        return self.query("SELECT * FROM files")
    
    def get_chunks(self):
        return self.query("SELECT * FROM chunks")
    
    def get_hosts(self):
        return self.query("SELECT * FROM hosts")