import sqlite3

conn = sqlite3.connect('knowledge.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check columns in knowledge_entries table
if ('knowledge_entries',) in tables:
    cursor.execute("PRAGMA table_info(knowledge_entries);")
    columns = cursor.fetchall()
    print("\nColumns in knowledge_entries:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

conn.close()