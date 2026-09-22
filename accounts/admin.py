from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'organization', 'theme_preference', 'created_at')
    list_filter = ('theme_preference', 'language', 'created_at')
    search_fields = ('user__username', 'user__email', 'organization')
    readonly_fields = ('created_at', 'updated_at')
