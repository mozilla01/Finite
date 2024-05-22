import threading
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Transaction
from django.db.models import Q
import os

User = get_user_model()


def delete_transaction(id):
    transactions = Transaction.objects.all().order_by('date', 'id')
    transaction = transactions.get(id=id)
    last_transaction = Transaction.objects.filter(~Q(id=transaction.id), Q(date__lt=transaction.date) | Q(date=transaction.date, id__lt=transaction.id), user=transaction.user).order_by('date', 'id').last()
    # prev_balance = last_transaction.init_balance if last_transaction else transaction.user.starting_balance
    newer_transactions = Transaction.objects.filter(Q(date__gt=transaction.date) | Q(date=transaction.date, id__gt=transaction.id), user=transaction.user).order_by('date', 'id')
    if last_transaction:
        print(last_transaction.description)
    transaction.receipt and os.path.isfile(transaction.receipt.path) and os.remove(transaction.receipt.path)
    user = User.objects.get(id=transaction.user.id)
    user.balance += 0 - transaction.amount if transaction.type == 'I' else transaction.amount
    user.save()
    transaction.delete()
    print('Newer Transactions:')
    for newer_transaction in newer_transactions:
        print(newer_transaction.description)
    for newer_transaction in newer_transactions:
        # newer_transaction.init_balance = prev_balance - newer_transaction.amount if newer_transaction.type == 'E' else prev_balance + newer_transaction.amount
        newer_transaction.save()
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
