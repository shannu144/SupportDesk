from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.tickets.views import TicketCategoryViewSet, SupportTicketViewSet

router = DefaultRouter()
router.register(r'categories', TicketCategoryViewSet, basename='ticket-category')
router.register(r'tickets', SupportTicketViewSet, basename='support-ticket')

urlpatterns = [
    path('', include(router.urls)),
]
