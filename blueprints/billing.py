from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_required
from . import billing
from app import db
from app import BillingForm
from app import Shop, Product, Transaction

@billing.route('/billing', methods=['GET', 'POST'])
@login_required
def manage_billing():
    form = BillingForm()
    if form.validate_on_submit():
        shop = Shop.query.filter_by(user_id=current_user.id).first()
        if shop:
            product = Product.query.filter_by(sku=form.sku.data, shop_id=shop.id).first()
            if product:
                transaction = Transaction(
                    product_id=product.id,
                    quantity=form.quantity.data,
                    total_amount=form.quantity.data * product.selling_price,
                    shop=shop
                )
                db.session.add(transaction)
                db.session.commit()
                flash('Bill generated!', 'success')
                return redirect(url_for('billing.manage_billing'))  # Specify the full endpoint name
            else:
                flash('Product not found in your shop!', 'danger')
        else:
            flash('No shop found for the current user.', 'danger')
    return render_template('billing.html', form=form)
