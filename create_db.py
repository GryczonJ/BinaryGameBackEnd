"""
Simple script to create all database tables from scratch.
Run this to initialize the database.
"""
from db import Base, engine
from models import User, Session, Puzzle, StoryPuzzle, DailyPuzzle, Solve, DailyRanking, AiHint

print("Creating all tables from models (if they don't exist)...")
Base.metadata.create_all(bind=engine)

print("✅ Database tables created successfully!")
print("\nTables created:")
for table in Base.metadata.sorted_tables:
    print(f"  - {table.name}")
