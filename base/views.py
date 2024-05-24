from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework.response import Response
from django.views import View
from rest_framework.views import APIView
from .models import Category, Source, Transaction, Bill
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.parsers import FormParser, MultiPartParser
from .serializers import CategorySerializer, SourceSerializer, TransactionSerializer, ProfileDetailsSerializer, GraphRequestSerializer
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from .utils import send_alert_mail, delete_transaction
from .utils import generate_graphs
import os
import json

User = get_user_model()

@login_required(login_url='login')
def index(request):

    categories = Category.objects.filter(user=request.user)
    sources = Source.objects.filter(user=request.user)

    context = {
        'categories': categories,
        'sources': sources,
    }
    return render(request, 'index.html', context=context)


class RenderGraphs(LoginRequiredMixin, APIView):
    login_url = 'login'

    def post(self, request):
        serializer = GraphRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            first_date = data['first_date']
            second_date = data['second_date']
            user = User.objects.get(id=request.user.id)
            start_date = None
            end_date = None
            if first_date > second_date:
                start_date = second_date
                end_date = first_date
            else:
                start_date = first_date
                end_date = second_date

            context = generate_graphs(user, start_date, end_date)
            context['first_date'] = first_date
            context['second_date'] = second_date
            context = json.dumps(context)

            return Response(context, status=200)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=400)


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
        Transaction.objects.create(user=bill.host, type='I', amount=bill.amount, bill=bill, description=f'{request.user.username}s split for {bill.bill_name}', category=None, source=Source.objects.get(name='split', user=request.user)).save()
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

class UpdateTransaction(LoginRequiredMixin, APIView):
    login_url = 'login'

    def post(self, request, pk):
        transaction = Transaction.objects.get(id=pk)
        prev_amount = transaction.amount
        serializer = TransactionSerializer(instance=transaction, data=request.data)
        if serializer.is_valid():
            serializer.save()
            user = User.objects.get(id=request.user.id)
            user.balance -= int(serializer.data['amount']) - prev_amount
            user.save()
            newer_transactions = Transaction.objects.filter(Q(date__gt=transaction.date) | Q(date=transaction.date, id__gt=transaction.id), user=transaction.user).order_by('date', 'id')
            for newer_transaction in newer_transactions:
                newer_transaction.save()
            return Response(data=serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)
    

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
