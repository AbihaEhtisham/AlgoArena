import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# SQLite database (your "Escalade 3") location
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "algoarena.db")

# Ensure the instance directory exists
os.makedirs(INSTANCE_DIR, exist_ok=True)
