from djoser.serializers import UserSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserSerializer(UserSerializer):
    is_staff = serializers.BooleanField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = ('id', 'username', 'is_staff')
