from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission


class Command(BaseCommand):
    help = 'Update Wagtail admin permission name to "Can access atom admin"'

    def handle(self, *args, **options):
        try:
            # Find the Wagtail admin access permission
            permission = Permission.objects.filter(
                codename='access_admin',
                content_type__app_label='wagtailadmin'
            ).first()
            
            if permission:
                if 'Wagtail admin' in permission.name:
                    old_name = permission.name
                    permission.name = permission.name.replace('Wagtail admin', 'atom admin')
                    permission.save(update_fields=['name'])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully updated permission: "{old_name}" -> "{permission.name}"'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Permission name is already updated or different: "{permission.name}"'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('Wagtail admin permission not found. It may not be created yet.')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating permission: {str(e)}')
            )


