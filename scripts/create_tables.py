#!/usr/bin/env python3
"""
Generate SQL to create analysis tables
"""

import os

def main():
    schema_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'database',
        'schema.sql'
    )
    
    print("🔨 RanchEye-02 Analysis - Database Setup SQL")
    print("=" * 80)
    print("\nCopy and paste the following SQL into your Supabase SQL Editor:\n")
    print("-" * 80)
    
    with open(schema_file, 'r') as f:
        sql = f.read()
        print(sql)
    
    print("-" * 80)
    print("\n✅ Steps to execute:")
    print("1. Go to https://supabase.com/dashboard/project/enoyydytzcgejwmivshz/sql")
    print("2. Click 'New query'")
    print("3. Paste the SQL above")
    print("4. Click 'Run'")
    print("\n💡 After creating tables, run:")
    print("   python scripts/supabase_admin.py create-sample")

if __name__ == "__main__":
    main()