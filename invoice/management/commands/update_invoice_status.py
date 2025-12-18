from django.core.management.base import BaseCommand
from invoice.utils import update_overdue_invoices

class Command(BaseCommand):
    help = 'Updates the status of invoices to "due" if the due date has passed and invoice is not paid'

    def handle(self, *args, **options):
        self.stdout.write('Updating invoice statuses...')
        updated_count = update_overdue_invoices()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} invoice(s) to "due" status'
            )
        )

