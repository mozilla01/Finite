from django.core.management.base import BaseCommand
from base.models import Category, Source, Transaction, Bill, User


class Command(BaseCommand):
    help = "Clears db except users"

    def handle(self, *args, **options):
        Category.objects.all().delete()
        Source.objects.all().delete()
        Transaction.objects.all().delete()
        Bill.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()