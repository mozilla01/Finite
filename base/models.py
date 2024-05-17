from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=50)


class Source(models.Model):
    name = models.CharField(max_length=50)


class Transaction(models.Model):
    class Type(models.TextChoices):
        EXPENSE = 'E', _('Expense')
        INCOME = 'I', _('Income')

    type = models.CharField(max_length=10, choices=Type.choices)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)
    source = models.ForeignKey(Source, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(default=timezone.now)
    amount = models.IntegerField()
    description = models.CharField(max_length=500)
