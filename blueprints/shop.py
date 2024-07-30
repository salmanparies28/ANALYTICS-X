from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_required
from . import shop
from app import db
from app import ShopForm
from app import Shop

@shop.route('/shop', methods=['GET', 'POST'])
@login_required
def manage_shop():
    form = ShopForm()
    if form.validate_on_submit():
        new_shop = Shop(name=form.name.data, address=form.address.data, phone=form.phone.data, owner=current_user)
        db.session.add(new_shop)
        db.session.commit()
        flash('Shop created!', 'success')
        return redirect(url_for('shop.manage_shop'))  # This is correct
    return render_template('shop.html', form=form)
