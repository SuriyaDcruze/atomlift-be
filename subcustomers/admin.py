from django.contrib import admin
from .models import SubCustomer


@admin.register(SubCustomer)
class SubCustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'customer', 'can_access_app', 'is_active', 'created_at')
    list_filter = ('can_access_app', 'is_active', 'created_at', 'customer')
    search_fields = ('name', 'email', 'customer__site_name', 'customer__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Sub-Customer Information', {
            'fields': ('customer', 'name', 'email', 'phone')
        }),
        ('Access Control', {
            'fields': ('can_access_app', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
