CREATE DATABASE IF NOT EXISTS photoshare;
USE photoshare;
DROP TABLE IF EXISTS Pictures CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

CREATE TABLE Users (
    user_id int4  AUTO_INCREMENT NOT NULL,
    first_name varchar(100) NOT NULL,
    last_name varchar(100) NOT NULL,
    password varchar(255) NOT NULL,
    gender varchar(6),
    email varchar(255) UNIQUE NOT NULL,
    hometown varchar(255),
    dob DATE NOT NULL,
  CONSTRAINT users_pk PRIMARY KEY (user_id),
  CHECK (first_name IS NOT NULL AND
         last_name IS NOT NULL AND
         password IS NOT NULL AND
         email IS NOT NULL AND
         dob IS NOT NULL)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob ,
  caption VARCHAR(255),
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
);
INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
