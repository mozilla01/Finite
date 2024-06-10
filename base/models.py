from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import date
from django.contrib.auth.models import AbstractUser
from django.db.models import Q


def upload_to(instance, filename):
    return "receipts/{filename}".format(filename=filename)

class User(AbstractUser):
    starting_balance = models.IntegerField(null=True, blank=True)
    balance = models.IntegerField(default=0, blank=True)
    pfp = models.ImageField(upload_to='profile_pictures/', default='static/images/default_pfp.webp')


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    budget = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = 'user', 'name'


class Source(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = 'user', 'name'



class Bill(models.Model):
    host = models.ForeignKey(User, on_delete=models.CASCADE)
    bill_name = models.CharField(max_length=50)
    amount = models.IntegerField()
    people = models.ManyToManyField(User, related_name='people')
    paid = models.ManyToManyField(User, related_name='paid', blank=True)


class Transaction(models.Model):
    class Type(models.TextChoices):
        EXPENSE = 'E', _('Expense')
        INCOME = 'I', _('Income')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, blank=True, null=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=10, choices=Type.choices)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
    source = models.ForeignKey(Source, null=True, on_delete=models.SET_NULL)
    date = models.DateField(default=date.today())
    init_balance = models.IntegerField(blank=True, null=True)
    amount = models.IntegerField()
    description = models.CharField(max_length=500)
    receipt = models.FileField(upload_to=upload_to, blank=True, null=True)

    def save(self, *args, **kwargs):
        print('----------------------------')
        print(f'Now saving transaction: {self.description}')
        print('Date:', self.date)
        if self.id:
            last_transaction = Transaction.objects.filter(~Q(id=self.id), Q(date__lt=self.date) | Q(date=self.date, id__lt=self.id), user=self.user).order_by('date', 'id').last()
        else:
            last_transaction = Transaction.objects.filter(~Q(id=self.id),date__lte=self.date, user=self.user).order_by('date', 'id').last()
        print('Self', self)
        print('ID of current transaction:', self.id)
        print('ID of last transaction:', last_transaction.id if last_transaction else None)
        for transaction in Transaction.objects.filter(user=self.user, date__lte=self.date).order_by('date', 'id'):
            print('i go next: Transaction:', transaction.description)
        if last_transaction:
            print('Last Transaction:', last_transaction.description, last_transaction.init_balance)
        prev_balance = last_transaction.init_balance if last_transaction else self.user.starting_balance
        print('Previous Balance:', type(prev_balance))
        print('self amount:', type(self.amount))
        self.init_balance = prev_balance - self.amount if self.type == 'E' else prev_balance + self.amount
        print('Balance:', self.init_balance)
        print('----------------------------')
        super(Transaction, self).save(*args, **kwargs)
