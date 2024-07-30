# blueprints/product.py
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_required
from . import product
from app import db
from app import ProductForm
from app import Shop, Product

@product.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        shop = Shop.query.filter_by(user_id=current_user.id).first()
        if shop:
            product = Product(sku=form.sku.data, name=form.name.data, net_price=form.net_price.data, selling_price=form.selling_price.data, shop_id=shop.id)
            db.session.add(product)
            db.session.commit()
            flash('Product added!', 'success')
            return redirect(url_for('product.add_product'))
        else:
            flash('No shop found for the current user.', 'danger')
    return render_template('add_product.html', form=form)
