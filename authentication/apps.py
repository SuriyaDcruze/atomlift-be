from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    
    def ready(self):
        """Update permission verbose names when app is ready"""
        # Connect to post_migrate signal to update permissions after migrations
        # This is the proper way to update database content after migrations
        post_migrate.connect(self.update_permission_names, sender=self)
    
    def update_permission_names(self, sender, **kwargs):
        """Update the 'Can access Wagtail admin' permission to 'Can access atom admin'"""
        from django.contrib.auth.models import Permission
        
        try:
            # Find the Wagtail admin access permission
            permission = Permission.objects.filter(
                codename='access_admin',
                content_type__app_label='wagtailadmin'
            ).first()
            
            if permission and 'Wagtail admin' in permission.name:
                permission.name = permission.name.replace('Wagtail admin', 'atom admin')
                permission.save(update_fields=['name'])
        except Exception:
            # If permission doesn't exist yet or there's an error, ignore it
            pass
