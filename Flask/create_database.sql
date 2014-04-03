DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS sessions;
CREATE TABLE users (username text, passhash int, user_role int);
CREATE TABLE sessions (username text, session text, date text);
INSERT INTO users (username, passhash, user_role) VALUES ("admin", '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', 1);