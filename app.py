from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///analytics_x.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def register_blueprints(app):
    from blueprints.auth import auth_bp
    from blueprints.shop import shop_bp
    from blueprints.product import product_bp
    from blueprints.billing import billing_bp
    from blueprints.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(dashboard_bp)

register_blueprints(app)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
