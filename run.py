import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f"==================================================")
    print(f" Meal Booking System is starting...")
    print(f" URL: http://127.0.0.1:{port}")
    print(f"==================================================")
    app.run(host="127.0.0.1", port=port, debug=debug)
