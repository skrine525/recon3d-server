from djoser.serializers import UserSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserSerializer(UserSerializer):
    is_staff = serializers.BooleanField(read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'is_staff', 'is_superuser',
            'display_name', 'date_joined'
        )

    def get_display_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.username
