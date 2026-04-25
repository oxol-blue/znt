# -*- coding: utf-8 -*-
import pymysql

DB_CONFIG = {
    'host': '85.137.245.183',
    'port': 3306,
    'user': 'znt',
    'password': 'znt',
    'database': 'znt',
    'charset': 'utf8mb4',
    'connect_timeout': 10
}

print("=" * 50)
print("Database Connection Test")
print("=" * 50)
print("\nConfig:")
print(f"  Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
print(f"  Database: {DB_CONFIG['database']}")
print(f"  User: {DB_CONFIG['user']}")
print()

conn = None
try:
    print("Connecting...")
    conn = pymysql.connect(**DB_CONFIG)
    print("Connection SUCCESS!")
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"MySQL Version: {version[0]}")
        
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()
        print(f"Current Database: {current_db[0]}")
        
        print("\nTables:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"  Found {len(tables)} tables:")
            for table in tables:
                print(f"    - {table[0]}")
        else:
            print("  WARNING: No tables found!")
            print("  Please import database first.")
            
    print("\nTest PASSED!")
    
except Exception as e:
    print(f"\nConnection FAILED!")
    print(f"Error: {e}")
    print("\nPossible reasons:")
    print("  1. Server not running")
    print("  2. Firewall blocking port 3306")
    print("  3. Wrong username/password")
    print("  4. Database 'znt' does not exist")
    
finally:
    if conn:
        conn.close()
        print("\nConnection closed")

print("\n" + "=" * 50)
