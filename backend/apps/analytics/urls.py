from django.urls import path
from apps.analytics.views import DashboardSummaryView, DashboardTrendsView

urlpatterns = [
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('dashboard/trends/', DashboardTrendsView.as_view(), name='dashboard_trends'),
]
