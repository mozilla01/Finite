from django.contrib import admin
from .models import Category, Source, Transaction, User, Bill

admin.site.register(Category)
admin.site.register(Source)
admin.site.register(Transaction)
admin.site.register(User)
admin.site.register(Bill)