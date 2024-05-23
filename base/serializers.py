from rest_framework import serializers
from .models import Category, Source, Transaction

class ProfileDetailsSerializer(serializers.Serializer):
    startBal = serializers.IntegerField(required=False)
    categories = serializers.JSONField(required=False)


class GraphRequestSerializer(serializers.Serializer):
    first_date = serializers.DateField()
    second_date = serializers.DateField()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    receipt = serializers.FileField(required=False)
    class Meta:
        model = Transaction
        fields = "__all__"
