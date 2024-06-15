import threading
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Transaction, Category
from django.db.models import Q, Sum
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

User = get_user_model()

custom_discrete_sequence = ['#1f77b4', '#ff7f0e', '#2ca02c']


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
    expenses = transactions.filter(type='E').order_by('date')
    incomelist = transactions.filter(type='I').order_by('date')
    
    # Pie chart for expenses
    if expenses.count() == 0:
        expenses_pie_html = '<div class="grid text-gray-800 w-full text-center place-items-center py-10">No expenses</div>'
    else:
        df = pd.DataFrame(list(expenses.values("category__name", "amount")))
        fig = px.pie(df, values='amount', names='category__name', title=f'Expenses by Category between {start_date} and {end_date}', color_discrete_sequence=px.colors.qualitative.Set3)
        expenses_pie_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    # Pie chart for income
    if incomelist.count() == 0:
        income_pie_html = '<div class="grid text-gray-800 w-full text-center place-items-center py-10">No income</div>'
    else:
        df = pd.DataFrame(list(incomelist.values("source__name", "amount")))
        fig = px.pie(df, values='amount', names='source__name', title=f'Income by Source between {start_date} and {end_date}', color_discrete_sequence=px.colors.qualitative.Set3)
        income_pie_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    # Mixed bar chart for expenses and income over latest 6 months
    if Transaction.objects.filter(user=user).count() == 0:
        mixed_bar_html = '<div class="text-gray-800 h-full w-full text-center py-10">No expenses or income</div>'
    else:
        df = pd.DataFrame(list(Transaction.objects.filter(user=user).values("date__month", "amount", "type")))
        fig = px.bar(df, x='date__month', y='amount', color='type', title='Expenses and Income over last 6 months', color_discrete_sequence=px.colors.qualitative.Set3)
        mixed_bar_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    # line chart for savings this month

    if transactions.count() > 0:
        df = pd.DataFrame(list(transactions.values("date", "init_balance")))
        fig = px.line(df, x='date', y='init_balance', title=f'Balance between {start_date} and {end_date}', color_discrete_sequence=px.colors.qualitative.Set3)
        savings_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        savings_html = '<div class="text-gray-800 h-full w-full text-center py-10">Need more than 1 transaction</div>'

    # Render table
    table_html = ''
    mobile_html = ''

    if transactions.count() > 0:
        for transaction in transactions:
            if transaction.type == "E":
                table_html += f'<tr class="border-t border-black hover:bg-gray-300 cursor-pointer" onclick="showTransactionDetails({transaction.id}, {transaction.amount}, \'\', {transaction.category.id}, \'{transaction.description}\', \'{transaction.date}\', \'{transaction.receipt}\')">'
                mobile_html += f'<div class="flex gap-4 p-4 border border-black w-full rounded bg-gradient-to-r from-red-200 via-orange-200 to-red-400" onclick="showTransactionDetails({transaction.id}, {transaction.amount}, \'\', {transaction.category.id}, \'{transaction.description}\', \'{transaction.date}\', \'{transaction.receipt}\')">'
            else:
                table_html += f'<tr class="border-t border-black hover:bg-gray-300 cursor-pointer" onclick="showTransactionDetails({transaction.id}, {transaction.amount}, {transaction.source.id}, \'\', \'{transaction.description}\', \'{transaction.date}\', \'{transaction.receipt}\')">'
                mobile_html += f'<div class="flex gap-4 p-4 border border-black w-full rounded bg-gradient-to-r from-red-200 via-orange-200 to-red-400" onclick="showTransactionDetails({transaction.id}, {transaction.amount}, {transaction.source.id}, \'\', \'{transaction.description}\', \'{transaction.date}\', \'{transaction.receipt}\')">'
            table_html += f'''
            <td class="px-6 py-4">{transaction.id}</td>
            <td class="px-6 py-4">{transaction.date}</td>
            '''
            if transaction.type == "E":
                table_html += f'''
                <td class="px-6 py-4 text-red-600">{transaction.amount}</td>
                <td class="px-6 py-4">{transaction.category.name}</td>
                '''
                mobile_html += f'''
                                        <div class="basis-1/4">
                                        <div class="text-slate-500">ID</div>
                                        <div class="text-slate-500">Date</div>
                                        <div class="text-slate-500">Amount</div>
                                        <div class="text-slate-500">Category</div>
                                        <div class="text-slate-500">Desc</div>
                                        <div class="text-slate-500">Initial bal.</div>
                                        </div>
                                        <div class="basis-3/4">
                                        <div>{transaction.id}</div>
                                        <div>{transaction.date}</div>
                                        <div>{transaction.amount}</div>
                                        <div>{transaction.category.name}</div>
                                        <div>{transaction.description}</div>
                                        <div>{transaction.init_balance}</div>
                                        </div>
                                    </div> 
                '''
            else:
                table_html += f'''
                <td class="px-6 py-4 text-green-600">{transaction.amount}</td>
                <td class="px-6 py-4">{transaction.source.name}</td>
                '''
                mobile_html += f'''
                                        <div class="basis-1/4">
                                        <div class="text-slate-500">ID</div>
                                        <div class="text-slate-500">Date</div>
                                        <div class="text-slate-500">Amount</div>
                                        <div class="text-slate-500">Source</div>
                                        <div class="text-slate-500">Desc</div>
                                        <div class="text-slate-500">Initial bal.</div>
                                        </div>
                                        <div class="basis-3/4">
                                        <div>{transaction.id}</div>
                                        <div>{transaction.date}</div>
                                        <div>{transaction.amount}</div>
                                        <div>{transaction.source.name}</div>
                                        <div>{transaction.description}</div>
                                        <div>{transaction.init_balance}</div>
                                        </div>
                                    </div> 
                '''
            table_html += f'''
            <td class="px-6 py-4">{transaction.description}</td>
            <td class="px-6 py-4 text-black">{transaction.init_balance}</td>
            </tr>
            '''
    else:
        table_html = '<div class="text-gray-800 h-full w-full text-center py-10">No transactions</div>'
        mobile_html = '<p class="text-gray-600">No transactions to display</p>'

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
    category_budgets_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    context = {
        'expense_pie': expenses_pie_html,
        'income_pie': income_pie_html,
        'mixed_bar': mixed_bar_html,
        'savings': savings_html,
        'category_budgets': category_budgets_html,
        'budget_overrun': budget_overrun,
        'table': table_html,
        'mobile': mobile_html
    }
    
    return context
