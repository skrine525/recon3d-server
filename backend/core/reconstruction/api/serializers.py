from rest_framework import serializers
from reconstruction.models import InitialMaskFile, HoughPreviewFile

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

class CalculateHoughSerializer(serializers.Serializer):
    plan_file_id = serializers.UUIDField(required=True)
    user_mask_file_id = serializers.UUIDField(required=True)

class HoughPreviewFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    class Meta:
        model = HoughPreviewFile
        fields = ['id', 'plan_upload_file_id', 'user_mask_upload_file_id', 'created_at', 'created_by', 'file_path', 'url']
        read_only_fields = fields

    def get_url(self, obj):
        from core import config
        from urllib.parse import urljoin
        base = getattr(config, 'APPLICATION_URL', '')
        media_url = '/media/'
        return urljoin(urljoin(base, media_url), obj.file_path) if obj.file_path else None 