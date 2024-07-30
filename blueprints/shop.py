from flask import Blueprint, request, render_template, redirect, url_for
from models import db, Shop

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/create_shop', methods=['GET', 'POST'])
def create_shop():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        street = request.form['street']
        city = request.form['city']
        district = request.form['district']
        state = request.form['state']
        pincode = request.form['pincode']
        phone_number = request.form['phone_number']
        shop_type = request.form['shop_type']
        new_shop = Shop(name=name, address=address, street=street, city=city, district=district, state=state, pincode=pincode, phone_number=phone_number, shop_type=shop_type)
        db.session.add(new_shop)
        db.session.commit()
        return redirect(url_for('shop.view_shops'))
    return render_template('create_shop.html')

@shop_bp.route('/view_shops')
def view_shops():
    shops = Shop.query.all()
    return render_template('view_shops.html', shops=shops)
