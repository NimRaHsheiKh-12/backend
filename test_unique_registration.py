from src.main import app
from fastapi.testclient import TestClient
import uuid

# Create a test client
client = TestClient(app)

# Generate a unique email
unique_email = f'test_{uuid.uuid4()}@example.com'
print(f'Testing registration endpoint with unique email: {unique_email}...')
try:
    response = client.post('/auth/register', json={'email': unique_email, 'password': 'testpassword123'})
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.json()}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()