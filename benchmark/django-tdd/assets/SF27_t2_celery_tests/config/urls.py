from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.notifications.views import NotificationViewSet

router = DefaultRouter()
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('api/', include(router.urls)),
]
