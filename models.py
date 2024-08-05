from app import app, db
from datetime import datetime

class Organisation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    company_size = db.Column(db.String(50), nullable=False)
    subscription_type = db.Column(db.String(50), nullable=False)
    end_date = db.Column(db.Date, nullable=False)

class ProductCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    product_list = db.relationship('Product', backref='category', lazy=True)
    inventory_list = db.relationship('Inventory', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    SKU = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    net_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    seller = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=True)  # Allow null if category not mandatory
    inventory = db.relationship('Inventory', backref='product', lazy=True)

    def restock(self, additional_quantity):
        self.quantity += additional_quantity
        db.session.commit()

class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)

class TransactionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_no = db.Column(db.Integer, unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    items = db.relationship('TransactionItem', backref='transaction', lazy=True)

class TransactionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction_record.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(100), nullable=True)  # Optional field
    district = db.Column(db.String(100), nullable=True)  # Optional field
    state = db.Column(db.String(100), nullable=True)  # Optional field
    pincode = db.Column(db.String(20), nullable=True)  # Optional field
    email = db.Column(db.String(100), nullable=True)  # Optional field

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=True)  # Allow NULL
    quantity = db.Column(db.Integer, nullable=False)

    @property
    def product_name(self):
        return self.product.name

    @property
    def category_name(self):
        return self.category.name if self.category else "No Category"

    def restock(self, additional_quantity):
        self.quantity += additional_quantity
        db.session.commit()

with app.app_context():
    db.create_all()
