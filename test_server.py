import asyncio
from src.main import app
import uvicorn

if __name__ == "__main__":
    # Test importing and running the app
    print("Testing app import...")
    try:
        # Try to create the app
        print("App created successfully")
        
        # Try to run the server
        print("Starting server on port 8000...")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        print(f"Error running server: {e}")
        import traceback
        traceback.print_exc()