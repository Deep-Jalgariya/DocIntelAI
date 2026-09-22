from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'document', 'details', 'timestamp')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('user__username', 'details', 'document__title')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
