from django.contrib import admin
from .models import Category, Source, Transaction, User

admin.site.register(Category)
admin.site.register(Source)
admin.site.register(Transaction)
admin.site.register(User)