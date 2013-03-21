
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
DROP TABLE IF EXISTS modifications;
CREATE TABLE modifications(
	id VARCHAR(300) PRIMARY KEY NOT NULL, /* SHA256 */
	date_modified DATE NOT NULL,
	chunks INTEGER NOT NULL,
	file_id INTEGER NOT NULL REFERENCES files(id)
);

DROP TRIGGER IF EXISTS drop_modifications;
CREATE TRIGGER drop_modifications
AFTER DELETE ON files
BEGIN
	DELETE FROM modifications WHERE file_id=OLD.id;
END;