from djoser.serializers import UserSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError

User = get_user_model()

class CustomUserSerializer(UserSerializer):
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'is_staff', 'is_superuser',
            'is_active', 'display_name', 'date_joined'
        )

    def get_display_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        
        return full_name if full_name else obj.username

class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    re_new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        if data['new_password'] != data['re_new_password']:
            raise serializers.ValidationError({"re_new_password": "Пароли не совпадают."})
        return data

class ChangeFlagSerializer(serializers.Serializer):
    """
    Универсальный сериализатор для изменения
    логических флагов is_staff и is_superuser.
    """
    value = serializers.BooleanField(required=True)
