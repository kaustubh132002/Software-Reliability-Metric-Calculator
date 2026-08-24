"""
Main Application Entry Point for Software Reliability Metric Calculator.
SEQA (Software Engineering and Quality Assurance).
"""

import os
from flask import Flask, render_template
from routes import main_bp
import models
import seed_data

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'seqa-reliability-calculator-secret-key-2026!'),
        DATABASE=os.path.join(app.root_path, 'database.db'),
    )

    if test_config:
        app.config.from_mapping(test_config)

    # Register blueprints
    app.register_blueprint(main_bp)

    # Initialize Database and Seed Sample Data
    with app.app_context():
        models.init_db(app.config['DATABASE'])
        seed_data.seed_initial_data(app.config['DATABASE'])

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Software Reliability Metric Calculator on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
