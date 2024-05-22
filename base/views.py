from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.response import Response
from django.views import View
from rest_framework.views import APIView
from .models import Category, Source, Transaction, Bill
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.parsers import FormParser, MultiPartParser
from .serializers import CategorySerializer, SourceSerializer, TransactionSerializer, ProfileDetailsSerializer
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from datetime import datetime
from django.db.models import Sum, Q
from .utils import send_alert_mail, delete_transaction
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

User = get_user_model()

@login_required(login_url='login')
def index(request):
    today = datetime.today().date()
    print(today.replace(day=1))
    first_date = request.GET.get('first-date', today.replace(day=1))
    second_date = request.GET.get('sec-date', today.replace(day=30))
    start_date = None
    end_date = None
    if first_date > second_date:
        start_date = second_date
        end_date = first_date
    else:
        start_date = first_date
        end_date = second_date

    categories = Category.objects.filter(user=request.user)
    sources = Source.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(user=request.user, date__range=[start_date, end_date]).order_by('date')
    expenses = transactions.filter(type='E').order_by('date')
    incomelist = transactions.filter(type='I').order_by('date')
    
    # Pie chart for expenses
    if expenses.count() == 0:
        expenses_pie_html = '<p class="p-4">No expenses in this range</p>'
    else:
        df = pd.DataFrame(list(expenses.values("category__name", "amount")))
        fig = px.pie(df, values='amount', names='category__name', title='Expenses by Category in this range')
        expenses_pie_html = fig.to_html(full_html=False)

    # Pie chart for income
    if incomelist.count() == 0:
        income_pie_html = '<p class="p-4">No income in this range</p>'
    else:
        df = pd.DataFrame(list(incomelist.values("source__name", "amount")))
        fig = px.pie(df, values='amount', names='source__name', title='Income by Source in this range')
        income_pie_html = fig.to_html(full_html=False)

    # Mixed bar chart for expenses and income over latest 6 months
    if Transaction.objects.filter(user=request.user).count() == 0:
        mixed_bar_html = '<p class="p-4">No transactions yet</p>'
    else:
        df = pd.DataFrame(list(Transaction.objects.filter(user=request.user).values("date__month", "amount", "type")))
        fig = px.bar(df, x='date__month', y='amount', color='type', title='Expenses and Income over last 6 months')
        mixed_bar_html = fig.to_html(full_html=False)

    # line chart for savings this month

    if transactions.count() > 0:
        df = pd.DataFrame(list(transactions.values("date", "init_balance")))
        fig = px.line(df, x='date', y='init_balance', title='Balance in this range')
        savings_html = fig.to_html(full_html=False)
    else:
        savings_html = '<p class="p-4">No transactions in this range</p>'

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
        'categories': categories,
        'transactions': transactions,
        'sources': sources,
        'expenses': expenses,
        'incomelist': incomelist,
        'expense_pie': expenses_pie_html,
        'income_pie': income_pie_html,
        'mixed_bar': mixed_bar_html,
        'savings': savings_html,
        'category_budgets': category_budgets_html,
        'budget_overrun': budget_overrun,
        'first_date': first_date,
        'second_date': second_date,
    }
    return render(request, 'index.html', context=context)


class Bills(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        created_bills = Bill.objects.filter(host=request.user)
        pending_bills = Bill.objects.filter(people=request.user)

        context = {
            'created_bills': created_bills,
            'pending_bills': pending_bills,
        }
        return render(request, 'bills.html', context=context)
    
    def post(self, request):
        data = request.POST
        bill = Bill.objects.create(host=request.user, bill_name=data['bill_name'], amount=data['amount'])
        people_list = data['people'].strip().split(',')
        email_list = []
        for person in people_list:
            if person:
                bill.people.add(User.objects.get(username=person))
                email_list.append(User.objects.get(username=person).email)
        send_alert_mail(subject='Bill added', content=f'You have been added to bill {bill.bill_name}. You owe {bill.amount} to {request.user.username}.', recipients=email_list)
        bill.save()
        return redirect('bills')


class PayBill(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, pk):
        bill = Bill.objects.get(id=pk)
        user = User.objects.get(id=request.user.id)
        host = User.objects.get(id=bill.host.id)
        bill.people.remove(request.user)
        bill.paid.add(request.user)
        bill.save()
        Transaction.objects.create(user=request.user, type='E', amount=bill.amount, bill=bill, description=f'Paid for {bill.bill_name}', category=Category.objects.get(name='bills', user=request.user), source=None).save()
        Transaction.objects.create(user=bill.host, type='I', amount=bill.amount, bill=bill, description=f'{request.user.username}\'s split for {bill.bill_name}', category=None, source=Source.objects.get(name='split', user=request.user)).save()
        send_alert_mail(subject='Split paid', content=f'{request.user.username} has paid {bill.amount} for bill {bill.bill_name}', recipients=[bill.host.email])
        user.balance -= bill.amount
        host.balance += bill.amount
        user.save()
        host.save()
        return redirect('bills')


class DeleteBill(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request, pk):
        bill = Bill.objects.get(id=pk)
        email_list = []
        for person in bill.paid.all():
            delete_transaction(Transaction.objects.get(user=person, bill=bill).id)
            delete_transaction(Transaction.objects.get(user=bill.host, bill=bill).id)
            email_list.append(person.email)
        send_alert_mail(subject='Bill deleted', content=f'{request.user.username} has deleted Bill {bill.bill_name}. Amount has been refunded to your wallet.', recipients=email_list)
        bill.delete()
        return redirect('bills')



class Profile(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        categories = Category.objects.filter(user=request.user)

        context = {
            'categories': categories,
        }
        return render(request, 'profile.html', context=context)

    def post(self, request):
        user = request.user
        user.pfp = request.FILES['pfp']
        user.save()
        return redirect('profile')

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            user.save()

            Category.objects.create(user=user, name='bills').save()
            Source.objects.create(user=user, name='split').save()
            return redirect('index')
        except:
            return render(request, 'signup.html', {'error': 'Username already exists'})
    else:
        return render(request, 'signup.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request=request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')

@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('index')


class CreateCategory(LoginRequiredMixin, APIView):
    login_url = 'login'

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            html = ''
            for category in Category.objects.filter(user=request.user):
                html += f'<option value="{category.id}">{category.name}</option>'
            return Response(data=html, status=201)
        else:
            return Response(serializer.errors, status=400)


class AddSource(LoginRequiredMixin, APIView):
    login_url = 'login'

    def post(self, request):
        serializer = SourceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            html = ''
            for source in Source.objects.filter(user=request.user):
                html += f'<option value="{source.id}">{source.name}</option>'
            return Response(data=html, status=201)
        else:
            return Response(serializer.errors, status=400)


class AddTransaction(LoginRequiredMixin, APIView):
    login_url = 'login'
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request):
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            group = Category.objects.get(id=serializer.data['category']) if serializer.data['category'] else Source.objects.get(id=serializer.data['source'])

            send = False
            user = User.objects.get(id=request.user.id)
            if serializer.data['type'] == 'E':
                user.balance -= serializer.data['amount']
                if user.balance < 0:
                    send = True
            else:
                user.balance += serializer.data['amount']
            user.save()

            newer_transactions = Transaction.objects.filter(Q(date__gt=serializer.data['date']) | Q(date=serializer.data['date'], id__gt=serializer.data['id']), user=request.user).order_by('date', 'id')
            prev_balance = serializer.data['init_balance']
            print(f'Prev balance: {prev_balance}')
            for transaction in newer_transactions:
                # transaction.init_balance = prev_balance + transaction.amount if transaction.type == 'I' else prev_balance - transaction.amount
                # prev_balance = transaction.init_balance
                transaction.save()


            html = f'''
            <tr class="border hover:bg-gray-300 cursor-pointer" onclick="showTransactionDetails({serializer.data['id']}, {serializer.data['amount']}, '', '{group.id}', '{serializer.data['description']}', '{serializer.data['date']}')">
                <td class="px-6 py-4">{serializer.data['id']}</td>
                <td class="px-6 py-4">{serializer.data['date']}</td>
                <td class="px-6 py-4">{serializer.data['amount']}</td>
                <td class="px-6 py-4">{group.name}</td>
                <td class="px-6 py-4">{serializer.data['description']}</td>
            </tr>
            '''
            if send:
                send_alert_mail('Balance alert', 'Your balance is negative. This email is simply an alert.', [user.email])
            return Response(data=html, status=201)
        else:
            return Response(serializer.errors, status=400)

class UpdateTransaction(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        data = request.POST
        user = User.objects.get(id=request.user.id)
        transaction = Transaction.objects.get(id=data['id'])
        transaction.date = data['date']
        if request.FILES:
            transaction.receipt and os.path.isfile(transaction.receipt.path) and os.remove(transaction.receipt.path)
            transaction.receipt = request.FILES['receipt']

        prev_amount = transaction.amount
        transaction.amount = int(data['amount'])
        user.balance -= int(data['amount']) - prev_amount
        print('Difference:', int(data['amount']) - prev_amount)
        print('New balance:', user.balance)
        user.save()
        transaction.description = data['description']
        if 'category' in data:
            transaction.category = Category.objects.get(id=data['category'])
        else:
            transaction.source = Source.objects.get(id=data['source'])
        transaction.save()
        newer_transactions = Transaction.objects.filter(Q(date__gt=transaction.date) | Q(date=transaction.date, id__gt=transaction.id), user=transaction.user).order_by('date', 'id')
        for newer_transaction in newer_transactions:
            newer_transaction.save()
        return redirect('index')
    

class DeleteTransaction(LoginRequiredMixin, View):
    login_url = 'login'

    def post(self, request):
        id = request.POST['id']
        delete_transaction(id)
        return redirect('index')


class UpdateProfile(LoginRequiredMixin, APIView):
    login_url = 'login'

    def post(self, request):
        serializer = ProfileDetailsSerializer(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            data = serializer.data
            if 'startBal' in data:
                user = User.objects.get(id=request.user.id)
                user.starting_balance = data['startBal']
                user.balance = data['startBal']
                user.save()
            if 'categories' in data:
                for category in data['categories']:
                    category_obj = Category.objects.get(id=int(category))
                    category_obj.budget = data['categories'][category]
                    category_obj.save()
            return Response(serializer.data, status=200)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=400)