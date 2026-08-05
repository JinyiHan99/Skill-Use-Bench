from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'channel', 'subject', 'body', 'status', 'sent_at', 'created_at']
        read_only_fields = ['status', 'sent_at', 'created_at']


class BulkNotificationSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField())
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    channel = serializers.ChoiceField(choices=['email', 'sms', 'push'], default='email')
