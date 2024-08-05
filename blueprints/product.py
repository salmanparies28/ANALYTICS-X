from flask import Blueprint, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from models import db, ProductCategory, Product, Inventory

product_bp = Blueprint('product', __name__)

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
    categories = ProductCategory.query.all()
    if request.method == 'POST':
        name = request.form['name']
        SKU = request.form['SKU']
        image = request.files['image']
        net_price = request.form['net_price']
        selling_price = request.form['selling_price']
        quantity = request.form['quantity']
        seller = request.form['seller']
        category_id = request.form.get('category_id', None)

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)
            image_url = os.path.join('uploads', filename)
        else:
            image_url = None

        new_product = Product(name=name, SKU=SKU, image=image_url, net_price=net_price, selling_price=selling_price, quantity=quantity, seller=seller, category_id=category_id)
        db.session.add(new_product)
        db.session.commit()

        new_inventory = Inventory(product_id=new_product.id, category_id=category_id, quantity=quantity)
        db.session.add(new_inventory)
        db.session.commit()

        return redirect(url_for('auth.home'))
    return render_template('add_product.html', categories=categories)



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

@product_bp.route('/restock_product', methods=['GET', 'POST'])
def restock_product():
    if request.method == 'POST':
        product_id = request.form['product_id']
        additional_quantity = int(request.form['additional_quantity'])

        product = Product.query.get(product_id)
        if product:
            product.restock(additional_quantity)
            inventory = Inventory.query.filter_by(product_id=product_id).first()
            if inventory:
                inventory.restock(additional_quantity)

        return redirect(url_for('product.inventory'))
    products = Product.query.all()
    return render_template('restock_product.html', products=products)
