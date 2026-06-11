import sys
import os
from flask import Flask
from flask_cors import CORS

# Add parent directory to path to allow 'src' imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.blueprints.articles import articles_bp
from src.blueprints.users import users_bp

def create_app():
    app = Flask(__name__)
    CORS(app) # Enable CORS for all routes
    
    # Register blueprints
    app.register_blueprint(articles_bp, url_prefix='/api/articles')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    @app.route('/health')
    def health():
        return {"status": "ok"}
        
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
