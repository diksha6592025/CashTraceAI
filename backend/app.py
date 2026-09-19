import os
from flask import Flask, send_from_directory, send_file, Response
from flask_cors import CORS
from config import Config

BASE_DIR = getattr(Config, 'BASE_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, 'frontend'))

def create_app():
    app = Flask(__name__, static_folder=None, static_url_path=None)
    app.config.from_object(Config)
    CORS(app)

    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # Register API routes
    from backend.routes import api_bp
    app.register_blueprint(api_bp)

    @app.route('/', methods=['GET'])
    def home():
        return render_file('index.html')

    @app.route('/safety', methods=['GET'])
    @app.route('/safety.html', methods=['GET'])
    def safety():
        return render_file('safety.html')

    @app.route('/about', methods=['GET'])
    @app.route('/about.html', methods=['GET'])
    def about():
        return render_file('about.html')

    @app.route('/images/<path:filename>', methods=['GET'])
    def serve_images(filename):
        images_dir = os.path.join(FRONTEND_DIR, 'images')
        target = os.path.join(images_dir, filename)
        if os.path.isfile(target):
            return send_from_directory(images_dir, filename)
        return ('', 404)

    @app.route('/<path:page_name>', methods=['GET'])
    def serve_any(page_name):
        clean = page_name.replace('-', '_').strip('/')
        if 'about' in clean.lower():
            return render_file('about.html')
        if 'safety' in clean.lower():
            return render_file('safety.html')

        full_path = os.path.join(FRONTEND_DIR, page_name)
        if os.path.isfile(full_path):
            return send_from_directory(FRONTEND_DIR, page_name)

        if os.path.isfile(os.path.join(FRONTEND_DIR, f"{clean}.html")):
            return render_file(f"{clean}.html")

        return render_file('index.html')

    def render_file(filename):
        target = os.path.join(FRONTEND_DIR, filename)
        if os.path.isfile(target):
            with open(target, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(content, mimetype='text/html')
        return send_from_directory(FRONTEND_DIR, filename)

    return app