import threading
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Transaction

User = get_user_model()


def delete_transaction(id):
    transaction = Transaction.objects.get(id=id)
    user = User.objects.get(id=transaction.user.id)
    user.balance += 0 - transaction.amount if transaction.type == 'I' else transaction.amount
    user.save()
    transaction.delete()


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