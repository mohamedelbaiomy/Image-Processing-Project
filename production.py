"""
Production server configuration for the Frequency Domain Image Enhancement application.
This uses Waitress, a production-ready WSGI server for Windows environments.
"""
import os
import argparse
from waitress import serve
from app import app


def run_production_server(host='0.0.0.0', port=5000):
    """Run the application using a production WSGI server."""
    print(f"Starting production server at http://{host}:{port}")
    print("Press Ctrl+C to quit")

    # Ensure required directories exist
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    os.makedirs(os.path.join('static', 'results'), exist_ok=True)
    os.makedirs(os.path.join('static', 'img'), exist_ok=True)

    # Run the placeholder creation script if needed
    if not os.path.exists(os.path.join('static', 'img', 'placeholder.png')):
        try:
            import create_placeholders
            print("Created placeholder images")
        except Exception as e:
            print(f"Warning: Could not create placeholder images: {e}")

    # Start the production server
    serve(app, host=host, port=port, threads=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run the Frequency Domain Image Enhancement application in production mode')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind the server to')

    args = parser.parse_args()
    run_production_server(args.host, args.port)