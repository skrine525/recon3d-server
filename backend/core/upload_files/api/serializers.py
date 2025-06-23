from rest_framework import serializers
from upload_files.models import UploadedFile
from core import config
from urllib.parse import urljoin

class UploadedFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=True)
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'file_path', 'url', 'file_type', 'source_type', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'file_path', 'url', 'file_type', 'source_type', 'uploaded_by', 'uploaded_at']

    def validate_file(self, value):
        if not value.name.lower().endswith('.jpg'):
            raise serializers.ValidationError('Можно загружать только .jpg файлы')
        return value

    def get_url(self, obj):
        base = getattr(config, 'APPLICATION_URL', '')
        media_url = '/media/'
        if obj.file_path:
            return urljoin(urljoin(base, media_url), obj.file_path)
        return None

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['uploaded_by'] = user
        return super().create(validated_data) 