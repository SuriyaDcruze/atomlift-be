from django.core.management.base import BaseCommand
from Routine_services.utils import update_overdue_routine_services

class Command(BaseCommand):
    help = 'Updates the status of routine services to overdue if the date has passed'

    def handle(self, *args, **options):
        self.stdout.write('Updating routine service statuses...')
        update_overdue_routine_services()
        self.stdout.write(self.style.SUCCESS('Successfully updated routine service statuses'))
