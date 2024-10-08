from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
import os
from models import db, ProductCategory, Product, Inventory

product_bp = Blueprint('product', __name__)

UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Category Routes
@product_bp.route('/add_category', methods=['GET', 'POST'])
def add_category():
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name = request.form['name']
        existing_category = ProductCategory.query.filter_by(name=name, organisation_id=organisation_id).first()
        if existing_category:
              flash('Category name is already in use!', 'danger')
              return render_template('category.html', categories=ProductCategory.query.filter_by(organisation_id=organisation_id).all())  # Render the same page
        
        new_category = ProductCategory(name=name, organisation_id=organisation_id)
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('product.view_categories'))
    
    return render_template('category.html')

@product_bp.route('/category')
def view_categories():
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    categories = ProductCategory.query.filter_by(organisation_id=organisation_id).all()
    return render_template('category.html', categories=categories)

@product_bp.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = ProductCategory.query.get_or_404(category_id)
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        new_name = request.form['name']
        
        # Check if new category name already exists
        existing_category = ProductCategory.query.filter_by(name=new_name, organisation_id=organisation_id).first()
        if existing_category and existing_category.id != category.id:
            flash('Category name is already in use!', 'danger')
            return render_template('edit_category.html', category=category, error_message="Category name is already in use.")
        
        category.name = new_name
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('product.view_categories'))
    return render_template('edit_category.html', category=category)

@product_bp.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    category = ProductCategory.query.get_or_404(category_id)
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('product.view_categories'))

@product_bp.route('/check_category', methods=['POST'])
def check_category():
    name = request.form.get('name')
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')

    if not organisation_id:
        return jsonify({'exists': False})

    exists = ProductCategory.query.filter_by(name=name, organisation_id=organisation_id).first() is not None
    return jsonify({'exists': exists})

# Product Routes
@product_bp.route('/add_product', methods=['GET', 'POST'])
def add_product():
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    categories = ProductCategory.query.filter_by(organisation_id=organisation_id).all()
    if request.method == 'POST':
        name = request.form['name']
        SKU = request.form['SKU']
        net_price = request.form['net_price']
        selling_price = request.form['selling_price']
        quantity = request.form['quantity']
        seller = request.form['seller']
        category_id = request.form.get('category_id', None)

        # Check if SKU already exists
        existing_product = Product.query.filter_by(SKU=SKU, organisation_id=organisation_id).first()
        if existing_product:
            flash('SKU code is already in use!', 'danger')
            return render_template('add_product.html', categories=categories, error_message="SKU code is already in use!")
        
        new_product = Product(name=name, SKU=SKU, net_price=net_price, selling_price=selling_price, quantity=quantity, seller=seller, category_id=category_id, organisation_id=organisation_id)
        db.session.add(new_product)
        db.session.commit()

        new_inventory = Inventory(product_id=new_product.id, category_id=category_id, quantity=quantity, organisation_id=organisation_id)
        db.session.add(new_inventory)
        db.session.commit()

        flash('Product added successfully!', 'success')
        return redirect(url_for('product.add_product'))

    return render_template('add_product.html', categories=categories)

@product_bp.route('/view_products')
def view_products():
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    products = Product.query.filter_by(organisation_id=organisation_id).all()
    return render_template('view_products.html', products=products)

@product_bp.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    categories = ProductCategory.query.filter_by(organisation_id=organisation_id).all()
    if request.method == 'POST':
        product.name = request.form['name']
        product.SKU = request.form['SKU']
        product.category_id = request.form['category_id']
        product.net_price = request.form['net_price']
        product.selling_price = request.form['selling_price']
        product.quantity = request.form['quantity']
        product.seller = request.form['seller']
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('product.view_products'))
    
    return render_template('edit_product.html', product=product, categories=categories)

@product_bp.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    # Remove from Inventory if exists
    inventory = Inventory.query.filter_by(product_id=product.id).first()
    if inventory:
        db.session.delete(inventory)
    
    # Delete the product
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')

    return redirect(url_for('product.view_products'))

@product_bp.route('/check_sku', methods=['POST'])
def check_sku():
    sku = request.form.get('SKU')
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        return jsonify({'exists': False})

    exists = Product.query.filter_by(SKU=sku, organisation_id=organisation_id).first() is not None
    return jsonify({'exists': exists})

# Inventory Routes
@product_bp.route('/inventory', methods=['GET', 'POST'])
def inventory():
    organisation_id = session.get('organisation_id')
    user_email = session.get('user_email')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        product_id = request.form['product_id']
        additional_quantity = request.form['additional_quantity']
        inventory_item = Inventory.query.filter_by(product_id=product_id, organisation_id=organisation_id).first()
        if inventory_item:
            inventory_item.quantity += int(additional_quantity)
        else:
            new_inventory_item = Inventory(product_id=product_id, quantity=int(additional_quantity), organisation_id=organisation_id)
            db.session.add(new_inventory_item)
        db.session.commit()
        flash('Inventory updated successfully!', 'success')

    products = Product.query.filter_by(organisation_id=organisation_id).all()

    # Using left join to include categories even if not fetched
    inventories = db.session.query(
        Inventory,
        Product.name.label('product_name'),
        ProductCategory.name.label('category_name')
    ).select_from(Inventory).join(Product, Inventory.product_id == Product.id)\
     .outerjoin(ProductCategory, Product.category_id == ProductCategory.id)\
     .filter(Product.organisation_id == organisation_id).all()

    return render_template('inventory.html',products=products, inventories=inventories)

# Add this route to product.py
@product_bp.route('/low_inventory_count')
def low_inventory_count():
    organisation_id = session.get('organisation_id')
    if not organisation_id:
        return jsonify({'low_inventory': False})
    
    low_inventory_count = Inventory.query.filter_by(organisation_id=organisation_id).filter(Inventory.quantity < 15).count()
    return jsonify({'low_inventory': low_inventory_count > 0})

