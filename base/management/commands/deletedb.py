from django.core.management.base import BaseCommand, CommandError
from base.models import Category, Source, Transaction


class Command(BaseCommand):
    help = "Clears db except users"

    def handle(self, *args, **options):
        Category.objects.all().delete()
        Source.objects.all().delete()
        Transaction.objects.all().delete()
