import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('knowledge.db')
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(knowledge_entries);")
columns = cursor.fetchall()
print("Database columns:")
for col in columns:
    print(f"  {col[1]}: {col[2]} (nullable: {col[3] == 0})")

# Check if there are any existing records
cursor.execute("SELECT COUNT(*) FROM knowledge_entries;")
count = cursor.fetchone()[0]
print(f"\nTotal records: {count}")

if count > 0:
    cursor.execute("SELECT * FROM knowledge_entries LIMIT 1;")
    row = cursor.fetchone()
    print("\nSample record:")
    for i, col in enumerate(columns):
        print(f"  {col[1]}: {row[i]}")

conn.close()