from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.response import Response
from django.views import View
from rest_framework.views import APIView
from .models import Category, Source, Transaction, Bill
from rest_framework.permissions import IsAuthenticated
from .serializers import CategorySerializer, SourceSerializer, TransactionSerializer, ProfileDetailsSerializer
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from datetime import datetime
from django.db.models import Sum
from .utils import send_alert_mail
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

User = get_user_model()

@login_required(login_url='login')
def index(request):
    today = datetime.today()
    categories = Category.objects.filter(user=request.user)
    sources = Source.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(user=request.user, date__month=today.month).order_by('date')
    expenses = transactions.filter(type='E', date__month=today.month).order_by('date')
    incomelist = transactions.filter(type='I', date__month=today.month).order_by('date')
    print("income", incomelist)
    
    # Pie chart for expenses
    if expenses.count() == 0:
        expenses_pie_html = '<p class="p-4">No expenses this month</p>'
    else:
        df = pd.DataFrame(list(expenses.values("category__name", "amount")))
        fig = px.pie(df, values='amount', names='category__name', title='Expenses by Category this month')
        expenses_pie_html = fig.to_html(full_html=False)

    # Pie chart for income
    if incomelist.count() == 0:
        income_pie_html = '<p class="p-4">No income this month</p>'
    else:
        df = pd.DataFrame(list(incomelist.values("source__name", "amount")))
        print("income pie chart")
        print(df.head())
        fig = px.pie(df, values='amount', names='source__name', title='Income by Source this month')
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
        fig = px.line(df, x='date', y='init_balance', title='Balance this month')
        savings_html = fig.to_html(full_html=False)
    else:
        savings_html = '<p class="p-4">No transactions yet</p>'

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
        'sources': sources,
        'expenses': expenses,
        'incomelist': incomelist,
        'expense_pie': expenses_pie_html,
        'income_pie': income_pie_html,
        'mixed_bar': mixed_bar_html,
        'savings': savings_html,
        'category_budgets': category_budgets_html,
        'budget_overrun': budget_overrun,
    }
    return render(request, 'index.html', context=context)


class Bills(View):
    def get(self, request):
        created_bills = Bill.objects.filter(host=request.user, paid=False)
        pending_bills = Bill.objects.filter(people=request.user, paid=False)
        for bill in pending_bills:
            if request.user in bill.people.all():
                bill.to_pay = bill.amount / bill.people.count()
        
        for bill in created_bills:
            bill.to_pay = bill.amount / bill.people.count()

        context = {
            'created_bills': created_bills,
            'pending_bills': pending_bills,
        }
        return render(request, 'bills.html', context=context)
    
    def post(self, request):
        data = request.POST
        bill = Bill.objects.create(host=request.user, bill_name=data['bill_name'], amount=data['amount'])
        for person in data['people'].strip().split(','):
            if person:
                bill.people.add(User.objects.get(username=person))
        bill.save()
        return redirect('bills')


class PayBill(View):
    def post(self, request, pk):
        bill = Bill.objects.get(id=pk)
        amount = bill.amount / bill.people.count()
        bill.people.remove(request.user)
        bill.save()
        Transaction.objects.create(user=request.user, type='E', amount=amount, description=f'Paid for {bill.bill_name}', category=Category.objects.get(name='bills', user=request.user), source=None).save()
        return redirect('bills')



class Profile(View):
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


def logout_user(request):
    logout(request)
    return redirect('index')


class CreateCategory(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            html = ''
            for category in Category.objects.all():
                html += f'<option value="{category.id}">{category.name}</option>'
            return Response(data=html, status=201)
        else:
            return Response(serializer.errors, status=400)


class AddSource(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SourceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            html = ''
            for source in Source.objects.all():
                html += f'<option value="{source.id}">{source.name}</option>'
            return Response(data=html, status=201)
        else:
            return Response(serializer.errors, status=400)


class AddTransaction(APIView):
    permission_classes = [IsAuthenticated]

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


            html = f'''<tr class="border hover:bg-gray-300 cursor-pointer">
                <td class="border">{serializer.data['id']}</td>
                <td>{serializer.data['date']}</td>
                <td>{serializer.data['amount']}</td>
                <td>{group.name}</td>
                <td>{serializer.data['description']}</td>
            </tr>
            '''
            if send:
                # send_mail(subject='Balance alert', from_email=settings.DEFAULT_FROM_EMAIL, message='Your balance is negative', recipient_list=[user.email], fail_silently=False)
                send_alert_mail('Balance alert', 'Your balance is negative. This email is simply an alert.', user.email)
            return Response(data=html, status=201)
        else:
            return Response(serializer.errors, status=400)

class UpdateTransaction(View):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.POST
        user = User.objects.get(id=request.user.id)
        transaction = Transaction.objects.get(id=data['id'])
        transaction.date = data['date']

        prev_amount = transaction.amount
        transaction.amount = data['amount']
        user.balance += int(data['amount']) - prev_amount
        user.save()
        transaction.description = data['description']
        if 'category' in data:
            transaction.category = Category.objects.get(id=data['category'])
        else:
            transaction.source = Source.objects.get(id=data['source'])
        transaction.save()
        return redirect('index')
    

class DeleteTransaction(View):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        id = request.POST['id']
        transaction = Transaction.objects.get(id=id)
        user = User.objects.get(id=request.user.id)
        user.balance += 0 - transaction.amount if transaction.type == 'I' else transaction.amount
        user.save()
        transaction.delete()
        return redirect('index')


class UpdateProfile(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProfileDetailsSerializer(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            data = serializer.data
            if 'mainBal' in data:
                user = User.objects.get(id=request.user.id)
                user.balance = data['mainBal']
                user.save()
            for category in data['categories']:
                category_obj = Category.objects.get(id=int(category))
                category_obj.budget = data['categories'][category]
                category_obj.save()
            return Response(serializer.data, status=200)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=400)