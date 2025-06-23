from rest_framework import serializers
from .models import InitialMaskFile

class CalculateInitialMaskSerializer(serializers.Serializer):
    file_id = serializers.UUIDField(required=True)

class InitialMaskFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    class Meta:
        model = InitialMaskFile
        fields = ['id', 'source_upload_file_id', 'created_at', 'created_by', 'file_path', 'url']
        read_only_fields = fields

    def get_url(self, obj):
        from core import config
        from urllib.parse import urljoin
        base = getattr(config, 'APPLICATION_URL', '')
        media_url = '/media/'
        return urljoin(urljoin(base, media_url), obj.file_path) if obj.file_path else None 