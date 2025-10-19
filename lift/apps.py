from django.apps import AppConfig


class LiftConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lift'

    def ready(self):
        import lift.wagtail_hooks
