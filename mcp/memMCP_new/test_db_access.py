import sqlite3
import json

# Test database access
try:
    conn = sqlite3.connect('knowledge.db')
    cursor = conn.cursor()
    
    # Test inserting a record
    cursor.execute(
        "INSERT INTO knowledge_entries (title, content, type) VALUES (?, ?, ?)",
        ("Test Title", "Test Content", "business_knowledge")
    )
    conn.commit()
    print("Successfully inserted test record")
    
    # Test selecting records
    cursor.execute("SELECT * FROM knowledge_entries WHERE title = ?", ("Test Title",))
    result = cursor.fetchone()
    if result:
        print("Successfully retrieved test record:", result)
    else:
        print("No test record found")
    
    # Clean up
    cursor.execute("DELETE FROM knowledge_entries WHERE title = ?", ("Test Title",))
    conn.commit()
    print("Cleaned up test record")
    
    conn.close()
    
except Exception as e:
    print("Database error:", e)