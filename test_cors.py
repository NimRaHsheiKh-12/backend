from src.config import settings

print("Current CORS origins:")
for origin in settings.cors_origins:
    print(f"  - {origin}")

print(f"\nBackend CORS origins setting: {settings.backend_cors_origins}")