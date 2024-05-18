from rest_framework import serializers
from .models import Category, Source, Transaction

class ProfileDetailsSerializer(serializers.Serializer):
    mainBal = serializers.IntegerField(required=False)
    categories = serializers.JSONField()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
