-- Database initialization script for secure Python web API

-- Create database (if not exists)
-- This is handled by POSTGRES_DB environment variable

-- Create user (if not exists)
-- This is handled by POSTGRES_USER environment variable

-- Set up security configurations
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = 'server.crt';
ALTER SYSTEM SET ssl_key_file = 'server.key';

-- Enable row-level security
ALTER SYSTEM SET row_security = on;

-- Set secure connection parameters
ALTER SYSTEM SET statement_timeout = '30s';
ALTER SYSTEM SET lock_timeout = '10s';
ALTER SYSTEM SET idle_in_transaction_session_timeout = '60s';

-- Set secure authentication
ALTER SYSTEM SET password_encryption = 'scram-sha-256';  -- pragma: allowlist secret

-- Create extensions for security
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set up audit logging
CREATE EXTENSION IF NOT EXISTS "pgaudit";

-- Configure pgaudit
ALTER SYSTEM SET pgaudit.log = 'write, ddl';
ALTER SYSTEM SET pgaudit.log_catalog = off;
ALTER SYSTEM SET pgaudit.log_parameter = on;
ALTER SYSTEM SET pgaudit.log_relation = on;
ALTER SYSTEM SET pgaudit.log_statement_once = on;

-- Create audit schema
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO api_user;
GRANT CREATE ON SCHEMA public TO api_user;
GRANT USAGE ON SCHEMA audit TO api_user;

-- Set up connection limits
ALTER USER api_user CONNECTION LIMIT 20;

-- Create read-only user for monitoring
CREATE USER monitor_user WITH PASSWORD 'monitor_password';  -- pragma: allowlist secret
GRANT CONNECT ON DATABASE secure_api_db TO monitor_user;
GRANT USAGE ON SCHEMA public TO monitor_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitor_user;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO monitor_user;

-- Set up monitoring user permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO monitor_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT SELECT ON TABLES TO monitor_user;

-- Create backup user
CREATE USER backup_user WITH PASSWORD 'backup_password';  -- pragma: allowlist secret
GRANT CONNECT ON DATABASE secure_api_db TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;

-- Set up backup user permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;

-- Reload configuration
SELECT pg_reload_conf();
