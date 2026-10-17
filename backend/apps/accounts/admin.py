from django.contrib import admin
from apps.accounts.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'department')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
