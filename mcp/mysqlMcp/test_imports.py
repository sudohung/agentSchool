# Test script to check if dependencies are installed
import sys

print("Python version:", sys.version)
print()

try:
    import fastmcp
    print("OK fastmcp installed:", fastmcp.__version__)
except ImportError as e:
    print("ERROR fastmcp NOT installed:", e)
    print("Run: pip install fastmcp")

print()

try:
    import pymysql
    print("OK PyMySQL installed:", pymysql.__version__)
except ImportError as e:
    print("ERROR PyMySQL NOT installed:", e)

print()

try:
    import pydantic
    print("OK pydantic installed:", pydantic.__version__)
except ImportError as e:
    print("ERROR pydantic NOT installed:", e)
