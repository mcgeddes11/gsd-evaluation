import os
from app import create_app, db

config = os.getenv("FLASK_ENV", "production").capitalize() + "Config"
app = create_app(config)

if __name__ == "__main__":
    app.run()