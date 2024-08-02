from flask import Blueprint, render_template
import altair as alt
import pandas as pd
from app import db
from models import TransactionRecord

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    # Fetch data from the database
    transactions = db.session.query(TransactionRecord).all()

    # Process data into a DataFrame
    data = {
        'Date': [transaction.date.strftime('%Y-%m-%d') for transaction in transactions],
        'Quantity': [transaction.quantity for transaction in transactions],
        'Total Price': [transaction.total_price for transaction in transactions]
    }
    df = pd.DataFrame(data)

    # Aggregate data by date
    df_agg = df.groupby('Date').agg({'Quantity': 'sum', 'Total Price': 'sum'}).reset_index()

    # Create an Altair chart
    bar_chart = alt.Chart(df_agg).mark_bar().encode(
        x='Date:T',
        y='Quantity:Q',
        tooltip=['Date:T', 'Quantity:Q', 'Total Price:Q']
    ).properties(
        width=500,
        height=300,
        title='Transaction Quantities Over Time'
    )

    # Save the chart as HTML
    chart_html = bar_chart.to_html()

    # Aggregated data for the card
    total_leads = df['Quantity'].sum()
    total_money_spent = df['Total Price'].sum()
    conversion_rate = (total_leads / df['Quantity'].count()) * 100  # Example calculation

    return render_template(
        'dashboard.html',
        chart_html=chart_html,
        total_leads=total_leads,
        total_money_spent=total_money_spent,
        conversion_rate=conversion_rate
    )
