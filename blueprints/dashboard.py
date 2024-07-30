# blueprints/dashboard.py
from flask import render_template
from flask_login import login_required, current_user
from . import dashboard
from app import Shop, Transaction
import matplotlib.pyplot as plt
import io
import base64

@dashboard.route('/dashboard')
@login_required
def view_dashboard():
    shop = Shop.query.filter_by(user_id=current_user.id).first()
    transactions = Transaction.query.filter_by(shop_id=shop.id).all()

    dates = [t.date.strftime('%Y-%m-%d') for t in transactions]
    amounts = [t.total_amount for t in transactions]
    plt.figure(figsize=(10, 5))
    plt.plot(dates, amounts, marker='o')
    plt.xlabel('Date')
    plt.ylabel('Total Amount')
    plt.title('Sales Over Time')
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return render_template('dashboard.html', plot_url=plot_url)
