from flask import Blueprint, render_template, request, jsonify, session, flash
import pandas as pd
from app import db
from models import Product, TransactionRecord, TransactionItem, ProductCategory
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    organisation_id = session.get('organisation_id')
    if not organisation_id:
        flash('User is not logged in!', 'danger')
        return redirect(url_for('auth.login'))
    
    filter_type = request.args.get('filter', 'today')
    start_date, end_date = get_date_range(filter_type)

    chart_data = get_chart_data(organisation_id, start_date, end_date)
    return render_template('dashboard.html', chart_data=chart_data, filter_type=filter_type)

@dashboard_bp.route('/dashboard_data')
def dashboard_data():
    organisation_id = session.get('organisation_id')
    if not organisation_id:
        return jsonify({'error': 'User is not logged in!'}), 403

    filter_type = request.args.get('filter', 'today')
    start_date, end_date = get_date_range(filter_type)

    chart_data = get_chart_data(organisation_id, start_date, end_date)
    return jsonify(chart_data)

def get_date_range(filter_type):
    end_date = datetime.today()
    if filter_type == 'today':
        start_date = end_date
    elif filter_type == 'week':
        start_date = end_date - timedelta(days=7)
    elif filter_type == 'month':
        start_date = end_date - timedelta(days=30)
    elif filter_type == 'year':
        start_date = end_date - timedelta(days=365)
    else:
        # Custom date range logic
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            start_date = end_date
    return start_date, end_date

def get_chart_data(organisation_id, start_date, end_date):
    # Fetch and process data for product categories
    product_categories = db.session.query(ProductCategory.id, ProductCategory.name, db.func.count(Product.id)).join(Product).filter(ProductCategory.organisation_id == organisation_id).group_by(ProductCategory.id).all()
    category_data = [count for _, _, count in product_categories]
    category_names = [name for _, name, _ in product_categories]

    # Fetch and process data for top 5 selling products
    top_products = db.session.query(
        Product.name,
        db.func.sum(TransactionItem.quantity).label('total_quantity')
    ).select_from(TransactionItem).join(Product, TransactionItem.product_id == Product.id).join(TransactionRecord, TransactionItem.transaction_id == TransactionRecord.id).filter(
        TransactionRecord.date.between(start_date, end_date),
        Product.organisation_id == organisation_id
    ).group_by(
        Product.id
    ).order_by(
        db.desc('total_quantity')
    ).limit(5).all()
    top_product_data = [qty for _, qty in top_products]
    top_product_names = [name for name, _ in top_products]

    # Fetch and process data for least 5 selling products
    least_products = db.session.query(
        Product.name,
        db.func.sum(TransactionItem.quantity).label('total_quantity')
    ).select_from(TransactionItem).join(Product, TransactionItem.product_id == Product.id).join(TransactionRecord, TransactionItem.transaction_id == TransactionRecord.id).filter(
        TransactionRecord.date.between(start_date, end_date),
        Product.organisation_id == organisation_id
    ).group_by(
        Product.id
    ).order_by(
        'total_quantity'
    ).limit(5).all()
    least_product_data = [qty for _, qty in least_products]
    least_product_names = [name for name, _ in least_products]

    # Fetch and process data for transactions
    transactions = db.session.query(TransactionRecord).filter(TransactionRecord.date.between(start_date, end_date), TransactionRecord.organisation_id == organisation_id).all()
    transaction_data = {
        'Date': [transaction.date.strftime('%Y-%m-%d') for transaction in transactions],
        'Total Price': [transaction.total_price for transaction in transactions]
    }
    df_transaction = pd.DataFrame(transaction_data)
    df_transaction_agg = df_transaction.groupby('Date').agg({'Total Price': 'sum'}).reset_index()

    # Fetch and process data for net price and selling price
    price_data = db.session.query(
        TransactionRecord.date,
        db.func.sum(Product.net_price * TransactionItem.quantity).label('total_net_price'),
        db.func.sum(Product.selling_price * TransactionItem.quantity).label('total_selling_price')
    ).select_from(TransactionItem).join(Product, TransactionItem.product_id == Product.id).join(TransactionRecord, TransactionItem.transaction_id == TransactionRecord.id).filter(
        TransactionRecord.date.between(start_date, end_date),
        TransactionRecord.organisation_id == organisation_id
    ).group_by(
        TransactionRecord.date
    ).all()
    price_dates = [record.date.strftime('%Y-%m-%d') for record in price_data]
    net_prices = [record.total_net_price for record in price_data]
    selling_prices = [record.total_selling_price for record in price_data]

    return {
        'category_data': category_data,
        'category_names': category_names,
        'top_product_data': top_product_data,
        'top_product_names': top_product_names,
        'least_product_data': least_product_data,
        'least_product_names': least_product_names,
        'transaction_data': {
            'labels': df_transaction_agg['Date'].tolist(),
            'total_prices': df_transaction_agg['Total Price'].tolist()
        },
        'price_data': {
            'labels': price_dates,
            'net_prices': net_prices,
            'selling_prices': selling_prices
        }
    }
