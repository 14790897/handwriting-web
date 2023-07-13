CREATE DATABASE IF NOT EXISTS mydatabase;
USE mydatabase

CREATE TABLE user_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE, 
    password VARCHAR(255), 
    image BLOB,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
