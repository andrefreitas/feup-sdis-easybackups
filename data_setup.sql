
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS files;
CREATE TABLE files(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name VARCHAR(30) UNIQUE NOT NULL
);

DROP TABLE IF EXISTS modifications;
CREATE TABLE modifications(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	sha256 VARCHAR(300) NOT NULL,
	date_modified DATE,
	chunks INTEGER,
	file_id INTEGER REFERENCES files(id)
);

DROP TABLE IF EXISTS chunks;
CREATE TABLE chunks(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	number INTEGER NOT NULL,
	replication_degree INTEGER NOT NULL DEFAULT 0,
	minimum_replication_degree INTEGER NOT NULL,
	modification_id INTEGER NOT NULL REFERENCES modifications(id)
);

DROP TRIGGER IF EXISTS drop_modifications;
CREATE TRIGGER drop_modifications
AFTER DELETE ON files
BEGIN
	DELETE FROM modifications WHERE file_id=OLD.id;
END;

DROP TRIGGER IF EXISTS drop_chunks;
CREATE TRIGGER drop_chunks
AFTER DELETE ON modifications
BEGIN
	DELETE FROM chunks WHERE modification_id=OLD.id;
END;