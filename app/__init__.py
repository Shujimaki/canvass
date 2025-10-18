from flask import Flask
from .extensions import cache, limiter, redis_client
from .routes import bp as main_bp
from .filters import register_filters

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    cache.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(main_bp)

    register_filters(app)

    return app