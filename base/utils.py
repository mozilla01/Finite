import threading
from django.core.mail import send_mail
from django.conf import settings

class EmailThread(threading.Thread):
    def __init__(self, subject, content, recipient):
        self.subject = subject
        self.recipient = recipient
        self.content = content
        threading.Thread.__init__(self)

    def run (self):
        send_mail(self.subject, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[self.recipient], message=self.content, fail_silently=False)

def send_alert_mail(subject, content, recipient):
    EmailThread(subject, content, recipient).start()