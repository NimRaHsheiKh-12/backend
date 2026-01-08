import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.abspath('.'))

print("Current working directory:", os.getcwd())

# Import settings first to ensure .env is loaded
from src.config import settings
print(f'Database URL from settings: {settings.database_url}')

# Now import the database module
from src.database.database import check_db_connection, create_db_and_tables

print('Testing database connection...')
result = check_db_connection()
print(f'Connection result: {result}')

print('Testing model creation...')
try:
    create_db_and_tables()
    print('Models created successfully')
except Exception as e:
    print(f'Model creation failed: {e}')
    import traceback
    traceback.print_exc()