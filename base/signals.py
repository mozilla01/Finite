from django.core.signals import request_finished
from django.dispatch import receiver
from .models import Category, Source

def create_bill_objects(sender, user, request, **kwargs):
    if not Category.objects.filter(name='bills', user=user).exists():
        Category.objects.create(name='bills', user=user).save()
    if not Source.objects.filter(name='split', user=user).exists():
        Source.objects.create(name='split', user=user).save()
    print("Request finished!")