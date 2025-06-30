from rest_framework import serializers

class IdentificationInputSerializer(serializers.Serializer):
    reconstruction_id = serializers.IntegerField(required=True)
    file_id = serializers.UUIDField(required=True)
    scale = serializers.FloatField(required=True) 