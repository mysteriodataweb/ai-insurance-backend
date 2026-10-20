import os

# Must run before any `app` import: settings and the engine are created at import time.
os.environ["APP_ENV"] = "test"
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-enough-length-1234")
if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
