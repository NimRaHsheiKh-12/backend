from src.config import settings

print("Backend CORS Origins from settings:", settings.backend_cors_origins)
print("Processed CORS Origins:", settings.cors_origins)
print("Type of cors_origins:", type(settings.cors_origins))