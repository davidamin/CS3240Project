DROP TABLE IF EXISTS users;
CREATE TABLE users (username text, passhash int);
CREATE TABLE sessions (username text, session text, date text);