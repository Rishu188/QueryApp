from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize extensions (without app for now)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Configure LoginManager
login_manager.login_view = 'main.login'

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['UPLOAD_FOLDER'] = 'app/static/profile_photos'

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Import here to avoid circular imports
    from app.models import User

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprint
    from app.routes import main
    app.register_blueprint(main)

    # Create tables (only for development)
    with app.app_context():
        db.create_all()

    return app
