"""
Script to create the BinaryGame database on SQL Server
"""
import pyodbc

# Connect to SQL Server master database
try:
    conn = pyodbc.connect(
        'Driver={ODBC Driver 17 for SQL Server};'
        'Server=APL-5CG0516ZX4;'
        'Trusted_Connection=yes;'
        'Database=master;'
    )
    cursor = conn.cursor()
    
    # Create database
    cursor.execute("CREATE DATABASE BinaryGame")
    conn.commit()
    print("✅ Database 'BinaryGame' created successfully!")
    
    cursor.close()
    conn.close()
except Exception as e:
    if "already exists" in str(e):
        print("ℹ️  Database 'BinaryGame' already exists")
    else:
        print(f"❌ Error: {e}")
