from flask import Blueprint, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from models import db, ProductCategory, Product, Inventory

product_bp = Blueprint('product', __name__)

# Ensure the upload folder exists
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@product_bp.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        user_id = request.form['user_id']
        new_category = ProductCategory(name=name, user_id=user_id)
        db.session.add(new_category)
        db.session.commit()
        return redirect(url_for('product.view_categories'))
    return render_template('add_category.html')

@product_bp.route('/view_categories')
def view_categories():
    categories = ProductCategory.query.all()
    return render_template('view_category.html', categories=categories)

@product_bp.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        SKU = request.form['SKU']
        category_id = request.form['category_id']
        image = request.files['image']
        net_price = request.form['net_price']
        selling_price = request.form['selling_price']
        quantity = request.form['quantity']
        seller = request.form['seller']

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)
            image_url = os.path.join('uploads', filename)  
        else:
            image_url = None

        new_product = Product(name=name, SKU=SKU, category_id=category_id, image=image_url, net_price=net_price, selling_price=selling_price, quantity=quantity, seller=seller)
        db.session.add(new_product)
        db.session.commit()

        # Add the product to the Inventory table
        new_inventory = Inventory(product_id=new_product.id, category_id=category_id, quantity=quantity)
        db.session.add(new_inventory)
        db.session.commit()

        return redirect(url_for('product.view_products'))
    return render_template('add_product.html')


@product_bp.route('/view_products')
def view_products():
    products = Product.query.all()
    return render_template('view_products.html', products=products)

@product_bp.route('/inventory')
def inventory():
    inventories = Inventory.query.all()
    return render_template('inventory.html', inventories=inventories)