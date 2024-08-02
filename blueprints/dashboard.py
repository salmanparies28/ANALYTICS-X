from flask import Blueprint, render_template, request
import pandas as pd
from app import db
from models import Product, TransactionRecord
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    filter_type = request.args.get('filter', 'today')
    start_date, end_date = get_date_range(filter_type)

    # Fetch and process data for product categories
    product_categories = db.session.query(Product.category_id, db.func.count(Product.id)).group_by(Product.category_id).all()
    category_data = {cat: count for cat, count in product_categories}

    # Fetch and process data for top 5 selling products
    top_products = db.session.query(
        TransactionRecord.product_id,
        db.func.sum(TransactionRecord.quantity).label('total_quantity')
    ).filter(
        TransactionRecord.date.between(start_date, end_date)
    ).group_by(
        TransactionRecord.product_id
    ).order_by(
        db.desc('total_quantity')
    ).limit(5).all()
    top_product_data = {prod: qty for prod, qty in top_products}

    # Fetch and process data for least 5 selling products
    least_products = db.session.query(
        TransactionRecord.product_id,
        db.func.sum(TransactionRecord.quantity).label('total_quantity')
    ).filter(
        TransactionRecord.date.between(start_date, end_date)
    ).group_by(
        TransactionRecord.product_id
    ).order_by(
        'total_quantity'
    ).limit(5).all()
    least_product_data = {prod: qty for prod, qty in least_products}

    # Fetch and process data for transactions
    transactions = db.session.query(TransactionRecord).filter(TransactionRecord.date.between(start_date, end_date)).all()
    transaction_data = {
        'Date': [transaction.date.strftime('%Y-%m-%d') for transaction in transactions],
        'Total Price': [transaction.total_price for transaction in transactions]
    }
    df_transaction = pd.DataFrame(transaction_data)
    df_transaction_agg = df_transaction.groupby('Date').agg({'Total Price': 'sum'}).reset_index()

    chart_data = {
        'category_data': category_data,
        'top_product_data': top_product_data,
        'least_product_data': least_product_data,
        'transaction_data': {
            'labels': df_transaction_agg['Date'].tolist(),
            'total_prices': df_transaction_agg['Total Price'].tolist()
        }
    }

    return render_template('dashboard.html', chart_data=chart_data, filter_type=filter_type)

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
