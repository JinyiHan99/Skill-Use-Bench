from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification(self, notification_id):
    """Send a notification through the appropriate channel."""
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return

    try:
        if notification.channel == 'email':
            send_mail(
                subject=notification.subject,
                message=notification.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
            )
        elif notification.channel == 'sms':
            # SMS provider integration
            from .providers import send_sms
            send_sms(notification.user.phone, notification.body)
        elif notification.channel == 'push':
            from .providers import send_push
            send_push(notification.user.device_token, notification.subject, notification.body)

        notification.mark_sent()
    except Exception as exc:
        notification.mark_failed(exc)
        raise self.retry(exc=exc)


@shared_task
def send_bulk_notifications(user_ids, subject, body, channel='email'):
    """Send the same notification to multiple users."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    notifications = []
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            notif = Notification.objects.create(
                user=user,
                channel=channel,
                subject=subject,
                body=body,
            )
            notifications.append(notif.id)
        except User.DoesNotExist:
            continue

    for notif_id in notifications:
        send_notification.delay(notif_id)

    return len(notifications)
