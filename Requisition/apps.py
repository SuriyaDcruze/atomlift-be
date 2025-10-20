from django.apps import AppConfig


class RequisitionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Requisition'
    
    def ready(self):
        import Requisition.wagtail_hooks