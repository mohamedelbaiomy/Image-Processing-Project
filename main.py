import os
import sys
import webbrowser
from threading import Timer
from app import app


def open_browser():
    """Open the browser after a delay."""
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    # Create required directories if they don't exist
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    os.makedirs(os.path.join('static', 'results'), exist_ok=True)
    os.makedirs(os.path.join('static', 'img'), exist_ok=True)

    # Open browser after a short delay
    Timer(1.5, open_browser).start()

    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)