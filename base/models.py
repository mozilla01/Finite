from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)


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
    amount = models.IntegerField()
    description = models.CharField(max_length=500)
