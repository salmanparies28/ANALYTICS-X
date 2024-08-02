from flask import Blueprint, request, render_template, redirect, url_for, session, jsonify
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
        product_ids = request.form.getlist('products')  # Get list of selected product IDs
        new_category = ProductCategory(name=name)
        db.session.add(new_category)
        db.session.commit()

        # Associate selected products with the new category
        for product_id in product_ids:
            product = Product.query.get(product_id)
            if product:
                product.category_id = new_category.id
        db.session.commit()

        return redirect(url_for('product.view_categories'))

    products = Product.query.all()
    return render_template('add_category.html', products=products)


@product_bp.route('/view_categories')
def view_categories():
    categories = ProductCategory.query.all()
    return render_template('view_category.html', categories=categories)


@product_bp.route('/fetch_products')
def fetch_products():
    category_name = request.args.get('category')
    products = Product.query.join(ProductCategory).filter(ProductCategory.name == category_name).all()
    
    product_list = [{'id': product.id, 'name': product.name} for product in products]
    return jsonify(product_list)

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

@product_bp.route('/edit_product/<int:product_id>', methods=['GET'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('edit_product.html', product=product)

@product_bp.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)

    product.name = request.form['name']
    product.SKU = request.form['SKU']
    product.category_id = request.form['category_id']
    product.net_price = request.form['net_price']
    product.selling_price = request.form['selling_price']
    product.quantity = request.form['quantity']
    product.seller = request.form['seller']

    new_image = request.files.get('new_image')
    if new_image:
        filename = secure_filename(new_image.filename)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        new_image.save(image_path)
        product.image = os.path.join('uploads', filename)

    db.session.commit()
    return redirect(url_for('product.view_products'))

@product_bp.route('/delete_product/<int:product_id>', methods=['GET'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Remove from Inventory if exists
    inventory = Inventory.query.filter_by(product_id=product.id).first()
    if inventory:
        db.session.delete(inventory)
    
    # Delete the product
    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('product.view_products'))

@product_bp.route('/inventory')
def inventory():
    inventories = Inventory.query.all()
    return render_template('inventory.html', inventories=inventories)
