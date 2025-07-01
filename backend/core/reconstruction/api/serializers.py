from rest_framework import serializers
from reconstruction.models import InitialMaskFile, HoughPreviewFile, Reconstruction

class CalculateInitialMaskSerializer(serializers.Serializer):
    file_id = serializers.UUIDField(required=True)

class InitialMaskFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    class Meta:
        model = InitialMaskFile
        fields = ['id', 'source_upload_file_id', 'created_at', 'created_by', 'url']
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
        fields = ['id', 'plan_upload_file_id', 'user_mask_upload_file_id', 'created_at', 'created_by', 'url']
        read_only_fields = fields

    def get_url(self, obj):
        from core import config
        from urllib.parse import urljoin
        base = getattr(config, 'APPLICATION_URL', '')
        media_url = '/media/'
        return urljoin(urljoin(base, media_url), obj.file_path) if obj.file_path else None

class CalculateMeshSerializer(serializers.Serializer):
    plan_file_id = serializers.UUIDField(required=True)
    user_mask_file_id = serializers.UUIDField(required=True)

class ReconstructionSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    class Meta:
        model = Reconstruction
        fields = ['id', 'name', 'status', 'status_display', 'created_at', 'created_by', 'saved_at', 'url']
        read_only_fields = fields

    def get_url(self, obj):
        from core import config
        from urllib.parse import urljoin
        base = getattr(config, 'APPLICATION_URL', '')
        media_url = '/media/'
        return urljoin(urljoin(base, media_url), obj.mesh_file_path) if obj.mesh_file_path else None

    def get_name(self, obj):
        return obj.get_name()

    def get_status_display(self, obj):
        return obj.get_status_display()

class SaveReconstructionSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)

# Новый сериализатор для обновления комнат
class RoomsUpdateSerializer(serializers.Serializer):
    rooms = serializers.JSONField(required=True) 