# Supabase Management Scripts

This directory contains scripts for managing your Supabase project.

## Available Scripts

### 1. `test_supabase_connection.py`
Quick test to verify your Supabase connection is working.

```bash
python scripts/test_supabase_connection.py
```

### 2. `supabase_admin.py`
Basic administration tasks using the Supabase client library.

```bash
# List all tables
python scripts/supabase_admin.py list-tables

# List storage buckets
python scripts/supabase_admin.py list-buckets

# Create a new bucket
python scripts/supabase_admin.py create-bucket --name my-bucket --public

# Get database size info
python scripts/supabase_admin.py db-size

# Create sample data
python scripts/supabase_admin.py create-sample

# Get info about a specific table
python scripts/supabase_admin.py table-info --name analysis_configs

# Check API usage
python scripts/supabase_admin.py api-usage
```

### 3. `supabase_management.py`
Advanced management using the Supabase Management API.

```bash
# Show project overview
python scripts/supabase_management.py overview

# Setup analysis tables from schema.sql
python scripts/supabase_management.py setup-tables

# Enable useful PostgreSQL extensions
python scripts/supabase_management.py enable-extensions

# Create helper database functions
python scripts/supabase_management.py create-functions

# Setup webhooks
python scripts/supabase_management.py setup-webhooks

# Show API keys (masked)
python scripts/supabase_management.py show-keys

# Run complete setup
python scripts/supabase_management.py full-setup
```

### 4. `setup_database.py`
Original database setup script for creating tables and sample configs.

```bash
python scripts/setup_database.py
```

## Requirements

All scripts require:
- Python 3.8+
- Configured `.env` file with Supabase credentials
- Required Python packages (install via `pip install -r requirements.txt`)

## Capabilities

With these scripts and the Service Role Key, you can:

### Database Management
- Create, modify, and delete tables
- Run SQL migrations
- Create stored procedures and functions
- Enable PostgreSQL extensions
- Monitor database size and performance

### Storage Management
- Create and configure storage buckets
- Set bucket policies
- Upload/download files

### API Management
- Monitor API usage and limits
- Create webhooks for real-time events
- Deploy edge functions
- Manage authentication settings

### Data Operations
- Query all tables
- Insert, update, and delete data
- Execute RPC functions
- Create sample/test data

## Security Notes

⚠️ **Important**: The Service Role Key has full admin access. Never expose it in client-side code or commit it to public repositories.

## Limitations

While these scripts provide extensive management capabilities, some operations still require the Supabase Dashboard:
- Creating new projects
- Billing management
- Team/organization management
- Some advanced PostgreSQL configurations

For direct SQL execution, you can:
1. Use the Supabase Dashboard SQL Editor
2. Connect via a PostgreSQL client using the connection string
3. Use the generated SQL from these scripts