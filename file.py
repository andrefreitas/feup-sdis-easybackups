import re
import hashlib
import os
import datetime

CHUNK_SIZE=64000 

class InvalidPathError:
	pass


class File:
	def __init__(self, full_path):
		self.set_full_path(full_path)
		self.parse_name()

	def parse_name(self):
		file_extension_pattern="[a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+$"
		full_path=self.get_full_path()
		try:
			self.set_name(re.search(file_extension_pattern,full_path).group(0))
		except:
			raise InvalidPathError 
		
	def get_modification_date(self):
		full_path=self.get_full_path()
		t = os.path.getmtime(full_path)
		return str(datetime.datetime.fromtimestamp(t))
	
	def generate_file_id(self):
		modification_date=self.get_modification_date()
		full_path=self.get_full_path()
		file_id=hashlib.sha256(full_path+modification_date).hexdigest()
		self.set_file_id(file_id)
		
	def generate_chunks(self):
		f=open(self._full_path, "rb")
		i=0
		while True:
			chunk = f.read(CHUNK_SIZE)
			if (chunk!=""):	
				chunk_file=open(self._name.split(".")[0]+"_"+str(i)+".chunk", "wb")
				chunk_file.write(chunk)
				chunk_file.close()
				i+=1
			else:
				break
		f.close()
		return i
		
	def restore_file(self, path):
		os.chdir(path)
		dir_list = os.listdir(path)
		restored_file=open(self._name, "ab")
		chunks={}
		name_without_extension = self._name.split(".")[0]
		chunk_name_pattern = name_without_extension+"_([0-9]+)\.chunk"
		
		# Fetch and sort chunk files
		for file_name in dir_list:
			match = re.search(chunk_name_pattern, file_name)
			if (match):
				chunks[int(match.group(1))] = file_name
		
		# Write chunks to file
		for i in range(len(chunks)):
			os.chdir(path)
			chunk=open(str(chunks[i]), "rb")
			restored_file.write(chunk.read())
			chunk.close()
			
		restored_file.close()
					
	def set_full_path(self,full_path):
		self._full_path=full_path

	def get_full_path(self):
		return self._full_path

	def set_name(self,name):
		self._name=name

	def get_name(self):
		return self._name

	def set_file_id(self,file_id):
		self._file_id=file_id

	def get_file_id(self):
		return self._file_id
