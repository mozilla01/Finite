from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Category, Source, Transaction
from rest_framework.permissions import IsAuthenticated
from .serializers import CategorySerializer, SourceSerializer, TransactionSerializer
from django.contrib.auth.decorators import login_required
from datetime import datetime
import pandas as pd
import plotly.express as px

@login_required(login_url='login')
def index(request):
    today = datetime.today()
    categories = Category.objects.filter(user=request.user)
    sources = Source.objects.filter(user=request.user)
    expenses = Transaction.objects.filter(user=request.user, type='E')
    incomelist = Transaction.objects.filter(user=request.user, type='I')
    
    # Pie chart for expenses
    if expenses.count() == 0:
        expenses_pie_html = '<p class="p-4">No expenses this month</p>'
    else:
        df = pd.DataFrame(list(expenses.filter(date__month=today.month).values("category__name", "amount")))
        fig = px.pie(df, values='amount', names='category__name', title='Expenses by Category this month')
        expenses_pie_html = fig.to_html(full_html=False)

    # Pie chart for income
    if incomelist.count() == 0:
        income_pie_html = '<p class="p-4">No income this month</p>'
    else:
        df = pd.DataFrame(list(incomelist.filter(date__month=today.month).values("source__name", "amount")))
        fig = px.pie(df, values='amount', names='source__name', title='Income by Source this month')
        income_pie_html = fig.to_html(full_html=False)

    # Mixed bar chart for expenses and income over latest 6 months
    df = pd.DataFrame(list(Transaction.objects.filter(user=request.user).values("date__month", "amount", "type")))
    fig = px.bar(df, x='date__month', y='amount', color='type', title='Expenses and Income over last 6 months')
    mixed_bar_html = fig.to_html(full_html=False)
    print(df.head())

    context = {
        'categories': categories,
        'sources': sources,
        'expenses': expenses,
        'incomelist': incomelist,
        'expense_pie': expenses_pie_html,
        'income_pie': income_pie_html,
        'mixed_bar': mixed_bar_html,
    }
    return render(request, 'index.html', context=context)

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            user.save()
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

            html = f'''<tr class="border hover:bg-gray-300 cursor-pointer">
                <td class="border">{serializer.data['id']}</td>
                <td>{serializer.data['date']}</td>
                <td>{serializer.data['amount']}</td>
                <td>{group.name}</td>
                <td>{serializer.data['description']}</td>
            </tr>
            '''
            return Response(data=html, status=201)
        else:
            return Response(serializer.errors, status=400)
