
PRAGMA foreign_keys = ON;

/* The files tables describes all the files by their fullpath.*/
DROP TABLE IF EXISTS files;
CREATE TABLE files(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name VARCHAR(30) UNIQUE NOT NULL
);

/* A certain file can be modified several times so, for a given 
record from files, there are a lot records in files_modified.
*/
DROP TABLE IF EXISTS files_modified;
CREATE TABLE files_modified(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	file_id VARCHAR(300) NOT NULL, /* SHA256 */
	file INTEGER NOT NULL,
	date_modified DATE NOT NULL,
	chunks INTEGER NOT NULL,
	FOREIGN KEY(file) REFERENCES files(id)
);

/* When a file is deleted, all the records from filed_modified 
should be deleted */

DROP TRIGGER IF EXISTS delete_files_modified;
CREATE TRIGGER delete_files_modified
AFTER DELETE ON files
BEGIN
	DELETE FROM files_modified WHERE file=OLD.id;
END;