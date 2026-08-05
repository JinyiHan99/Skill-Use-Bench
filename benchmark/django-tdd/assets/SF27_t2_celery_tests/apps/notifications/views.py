from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Notification
from .serializers import NotificationSerializer, BulkNotificationSerializer
from .tasks import send_notification, send_bulk_notifications


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        notification = serializer.save(user=self.request.user)
        send_notification.delay(notification.id)

    @action(detail=False, methods=['post'])
    def bulk_send(self, request):
        serializer = BulkNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        count = send_bulk_notifications.delay(
            user_ids=serializer.validated_data['user_ids'],
            subject=serializer.validated_data['subject'],
            body=serializer.validated_data['body'],
            channel=serializer.validated_data['channel'],
        )
        return Response({'queued': True}, status=status.HTTP_202_ACCEPTED)
