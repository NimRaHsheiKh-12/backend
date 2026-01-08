from src.main import app
from fastapi.testclient import TestClient

# Create a test client
client = TestClient(app)

print('Testing registration endpoint...')
try:
    response = client.post('/auth/register', json={'email': 'test7@example.com', 'password': 'testpassword123'})
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.json()}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()