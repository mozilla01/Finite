import threading
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Transaction, Category, Source
from django.db.models import Q, Sum
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

User = get_user_model()


def delete_transaction(id):
    transactions = Transaction.objects.all().order_by('date', 'id')
    transaction = transactions.get(id=id)
    newer_transactions = Transaction.objects.filter(Q(date__gt=transaction.date) | Q(date=transaction.date, id__gt=transaction.id), user=transaction.user).order_by('date', 'id')

    # Delete receipt if exists
    transaction.receipt and os.path.isfile(transaction.receipt.path) and os.remove(transaction.receipt.path)
    user = User.objects.get(id=transaction.user.id)

    # Update balance
    user.balance += 0 - transaction.amount if transaction.type == 'I' else transaction.amount
    user.save()
    transaction.delete()

    # Update balance for newer transactions
    for newer_transaction in newer_transactions:
        newer_transaction.save() # Overriden save method in Transaction model will update balance
        # prev_balance = newer_transaction.init_balance


class EmailThread(threading.Thread):
    def __init__(self, subject, content, recipients):
        self.subject = subject
        self.recipients = recipients
        self.content = content
        threading.Thread.__init__(self)

    def run (self):
        send_mail(self.subject, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=self.recipients, message=self.content, fail_silently=False)


def send_alert_mail(subject, content, recipients):
    EmailThread(subject, content, recipients).start()


def generate_report(user, start_date, end_date):
    transactions = Transaction.objects.filter(user=user, date__gte=start_date, date__lte=end_date).order_by('date', 'id')
    if not transactions:
        return None
    transactions = transactions.values('date', 'amount', 'description', 'type')
    df = pd.DataFrame(transactions)
    df['init_balance'] = df['amount'].cumsum()
    fig = px.line(df, x='date', y='init_balance', title='Balance Over Time')
    fig.write_html('media/reports/report.html')
    return 'media/reports/report.html'


def generate_graphs(user, start_date, end_date):
    transactions = Transaction.objects.filter(user=user, date__range=[start_date, end_date]).order_by('date')
    categories = Category.objects.filter(user=user)
    sources = Source.objects.filter(user=user)
    expenses = transactions.filter(type='E').order_by('date')
    incomelist = transactions.filter(type='I').order_by('date')
    
    # Pie chart for expenses
    if expenses.count() == 0:
        expenses_pie_html = ''
    else:
        df = pd.DataFrame(list(expenses.values("category__name", "amount")))
        fig = px.pie(df, values='amount', names='category__name', title=f'Expenses by Category between {start_date} and {end_date}')
        expenses_pie_html = fig.to_html(full_html=False)

    # Pie chart for income
    if incomelist.count() == 0:
        income_pie_html = ''
    else:
        df = pd.DataFrame(list(incomelist.values("source__name", "amount")))
        fig = px.pie(df, values='amount', names='source__name', title=f'Income by Source between {start_date} and {end_date}')
        income_pie_html = fig.to_html(full_html=False)

    # Mixed bar chart for expenses and income over latest 6 months
    if Transaction.objects.filter(user=user).count() == 0:
        mixed_bar_html = ''
    else:
        df = pd.DataFrame(list(Transaction.objects.filter(user=user).values("date__month", "amount", "type")))
        fig = px.bar(df, x='date__month', y='amount', color='type', title='Expenses and Income over last 6 months')
        mixed_bar_html = fig.to_html(full_html=False)

    # line chart for savings this month

    if transactions.count() > 0:
        df = pd.DataFrame(list(transactions.values("date", "init_balance")))
        fig = px.line(df, x='date', y='init_balance', title=f'Balance between {start_date} and {end_date}')
        savings_html = fig.to_html(full_html=False)
    else:
        savings_html = ''

    # Render table
    table_html = ''

    for transaction in transactions:
        if transaction.type == "E":
            table_html += f'<tr class="border hover:bg-gray-300 cursor-pointer" onclick="showTransactionDetails({transaction.id}, {transaction.amount}, \'\', {transaction.category.id}, \'{transaction.description}\', \'{transaction.date}\', \'{transaction.receipt}\')">'
        else:
            table_html += f'<tr class="border hover:bg-gray-300 cursor-pointer" onclick="showTransactionDetails({transaction.id}, {transaction.amount}, {transaction.source.id}, \'\', \'{transaction.description}\', \'{transaction.date}\', \'{transaction.receipt}\')">'
        table_html += f'''
        <td class="px-6 py-4">{transaction.id}</td>
        <td class="px-6 py-4">{transaction.date}</td>
        '''
        if transaction.type == "E":
            table_html += f'''
            <td class="px-6 py-4 text-red-600">{transaction.amount}</td>
            <td class="px-6 py-4">{transaction.category.name}</td>
            '''
        else:
            table_html += f'''
            <td class="px-6 py-4 text-green-600">{transaction.amount}</td>
            <td class="px-6 py-4">{transaction.source.name}</td>
            '''
        table_html += f'''
        <td class="px-6 py-4">{transaction.description}</td>
        <td class="px-6 py-4 text-black">{transaction.init_balance}</td>
        </tr>
        '''
    print('HTML table:')
    print(table_html)

    # Category budgets 
    category_balances = []
    category_expenses = []
    category_names = []
    budget_overrun = []
    for category in categories:
         if category.budget:
            sum = expenses.filter(category=category).aggregate(Sum('amount'))['amount__sum'] or 0
            category_expenses.append(sum)
            if sum > category.budget:
                budget_overrun.append(category.name)
            category_balances.append(category.budget - sum)
            category_names.append(category.name)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(y=[category for category in category_names], x=category_expenses, orientation='h', marker=dict(
        color='rgba(246, 78, 139, 1.0)',
        line=dict(color='rgba(58, 71, 80, 1.0)', width=3)
    ), name='Expenses'))
    fig.add_trace(go.Bar(y=[category for category in category_names], x=category_balances, orientation='h', marker=dict(
        color='rgba(58, 71, 80, 0.2)',
        line=dict(color='rgba(58, 71, 80, 1.0)', width=3)
    ), name='Remaining Budget'))
    fig.update_layout(barmode='stack', title='Category Budgets this month')
    category_budgets_html = fig.to_html(full_html=False)

    context = {
        'expense_pie': expenses_pie_html,
        'income_pie': income_pie_html,
        'mixed_bar': mixed_bar_html,
        'savings': savings_html,
        'category_budgets': category_budgets_html,
        'budget_overrun': budget_overrun,
        'table': table_html
    }
    
    return context
