def register_blueprints(app):
    from .auth import auth_bp
    from .shop import shop_bp
    from .product import product_bp
    from .billing import billing_bp
    from .dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(dashboard_bp)
