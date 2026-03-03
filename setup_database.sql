-- Create the Adds database for Click Fraud Detection App
CREATE DATABASE IF NOT EXISTS Adds;
USE Adds;

-- Create users table for login/register functionality
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  username VARCHAR(100) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index on email for faster lookups
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_username ON users(username);

-- Confirm tables created
SELECT 'Database and tables created successfully!' AS status;
