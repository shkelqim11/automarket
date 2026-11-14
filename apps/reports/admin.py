from django.contrib import admin
from .models import Report
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["car", "reason", "reporter", "resolved", "created_at"]
    list_filter = ["resolved", "reason"]; list_editable = ["resolved"]
