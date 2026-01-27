"""
Drops and recreates the BinaryGame database, then creates all tables.
"""
import pyodbc
from db import engine, Base
from models import User, Session, Puzzle, StoryPuzzle, DailyPuzzle, Solve, DailyRanking, AiHint

print("Connecting to master database...")
# Connect to master to drop/create database
conn_str = r'DRIVER={ODBC Driver 17 for SQL Server};SERVER=(localdb)\MSSQLLocalDB;DATABASE=master;Trusted_Connection=yes;'
conn = pyodbc.connect(conn_str, autocommit=True)
cursor = conn.cursor()

print("Dropping BinaryGame database if it exists...")
try:
    cursor.execute("ALTER DATABASE BinaryGame SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    cursor.execute("DROP DATABASE BinaryGame")
    print("  ✓ Dropped existing database")
except Exception as e:
    print(f"  - Database didn't exist or couldn't be dropped: {e}")

print("Creating fresh BinaryGame database...")
cursor.execute("CREATE DATABASE BinaryGame")
print("  ✓ Database created")

cursor.close()
conn.close()

print("\nCreating all tables...")
Base.metadata.create_all(bind=engine)

print("\n✅ Database setup complete!")
print("\nTables created:")
for table in Base.metadata.sorted_tables:
    print(f"  - {table.name}")
