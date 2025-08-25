-- =====================================================
-- Book Review System - Database Setup Script
-- Version: 1.0
-- Date: December 2024
-- 
-- This script sets up the PostgreSQL database and user
-- for the Book Review System development environment.
-- 
-- Prerequisites:
-- - PostgreSQL 15+ installed and running
-- - psql command line tool available
-- =====================================================

-- Connect to PostgreSQL as superuser (postgres)
-- psql -U postgres -h localhost

-- Create the database
CREATE DATABASE brs_dev
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Create the application user
CREATE USER brs_user WITH PASSWORD 'dev_password';

-- Grant necessary privileges to the user
GRANT CONNECT ON DATABASE brs_dev TO brs_user;
GRANT USAGE ON SCHEMA public TO brs_user;
GRANT CREATE ON SCHEMA public TO brs_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO brs_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO brs_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO brs_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO brs_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO brs_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO brs_user;

-- Connect to the new database
-- \c brs_dev

-- Grant schema usage to the user
GRANT USAGE ON SCHEMA public TO brs_user;

-- Verify the setup
SELECT 
    datname as database_name,
    usename as owner
FROM pg_database 
WHERE datname = 'brs_dev';

SELECT 
    usename,
    usecreatedb,
    usesuper
FROM pg_user 
WHERE usename = 'brs_user';

-- =====================================================
-- Connection Information
-- =====================================================
-- 
-- Database: brs_dev
-- Host: localhost
-- Port: 5432
-- Username: brs_user
-- Password: dev_password
-- 
-- JDBC URL: jdbc:postgresql://localhost:5432/brs_dev
-- 
-- =====================================================
-- Next Steps
-- =====================================================
-- 
-- 1. Update application-dev.yml with these connection details
-- 2. Run the Spring Boot application
-- 3. Flyway will automatically create the schema
-- 4. Test data will be inserted automatically
-- 
-- =====================================================
