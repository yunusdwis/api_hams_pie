from flask import Flask
from flask_cors import CORS
from app.auth.routes import auth_bp
from app.persons.routes import persons_bp
from app.buildings.routes import buildings_bp
from app.counts.routes import counts_bp
from app.danger.routes import danger_bp
import argparse

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(persons_bp)
    app.register_blueprint(buildings_bp)
    app.register_blueprint(counts_bp)
    app.register_blueprint(danger_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run the Flask application')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the application on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=True)