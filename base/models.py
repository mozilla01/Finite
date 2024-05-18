from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    balance = models.IntegerField(default=0, blank=True)
    pfp = models.ImageField(upload_to='profile_pictures/', default='static/images/default_pfp.webp')

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    budget = models.IntegerField(null=True, blank=True)


class Source(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)


class Transaction(models.Model):
    class Type(models.TextChoices):
        EXPENSE = 'E', _('Expense')
        INCOME = 'I', _('Income')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=Type.choices)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
    source = models.ForeignKey(Source, null=True, on_delete=models.SET_NULL)
    date = models.DateField(default=timezone.now)
    init_balance = models.IntegerField(blank=True, null=True)
    amount = models.IntegerField()
    description = models.CharField(max_length=500)

    def save(self, *args, **kwargs):
        self.init_balance = User.objects.get(id=self.user.id).balance
        super(Transaction, self).save(*args, **kwargs)