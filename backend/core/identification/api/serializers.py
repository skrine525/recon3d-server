from rest_framework import serializers
from identification.models import Identification

class IdentificationInputSerializer(serializers.Serializer):
    reconstruction_id = serializers.IntegerField(required=True)
    file_id = serializers.UUIDField(required=True)

class IdentificationSerializer(serializers.ModelSerializer):
    display_status = serializers.SerializerMethodField()
    reconstruction = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Identification
        fields = ['id', 'created_at', 'created_by', 'reconstruction', 'status', 'display_status', 'x_value', 'y_value']
        read_only_fields = fields

    def get_display_status(self, obj):
        return obj.get_status_display() 