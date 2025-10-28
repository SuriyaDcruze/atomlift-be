from django.core.management.base import BaseCommand
from recurringInvoice.models import RecurringInvoice
from django.utils import timezone

class Command(BaseCommand):
    help = 'Test and manage recurring invoice renewals'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true', help='List all recurring invoices with renewal status')
        parser.add_argument('--renew', type=str, help='Renew a specific invoice by reference ID')
        parser.add_argument('--test', action='store_true', help='Test renewal functionality')

    def handle(self, *args, **options):
        if options['list']:
            self.list_invoices()
        elif options['renew']:
            self.renew_invoice(options['renew'])
        elif options['test']:
            self.test_renewal()
        else:
            self.show_help()

    def list_invoices(self):
        self.stdout.write(self.style.SUCCESS('Recurring Invoices with Renewal Status:'))
        self.stdout.write('=' * 60)
        
        invoices = RecurringInvoice.objects.all()
        for invoice in invoices:
            renewal_info = invoice.get_renewal_info()
            days = renewal_info['days_until_expiry']
            
            if days < 0:
                status = f"🚨 EXPIRED ({abs(days)} days ago)"
            elif days <= 7:
                status = f"⚠️ Expires in {days} days"
            elif days <= 30:
                status = f"🟡 Expires in {days} days"
            else:
                status = f"✅ Active ({days} days)"
            
            self.stdout.write(f"{invoice.reference_id}: {status}")
            self.stdout.write(f"  End Date: {invoice.end_date}")
            self.stdout.write(f"  Status: {invoice.status}")
            self.stdout.write(f"  Repeat Every: {invoice.repeat_every}")
            self.stdout.write('')

    def renew_invoice(self, reference_id):
        try:
            invoice = RecurringInvoice.objects.get(reference_id=reference_id)
            old_end_date = invoice.end_date
            
            success = invoice.renew_recurring_invoice()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully renewed {reference_id}!'
                    )
                )
                self.stdout.write(f'  Old End Date: {old_end_date}')
                self.stdout.write(f'  New End Date: {invoice.end_date}')
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Failed to renew {reference_id}'
                    )
                )
        except RecurringInvoice.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Invoice {reference_id} not found')
            )

    def test_renewal(self):
        self.stdout.write(self.style.SUCCESS('Testing Renewal Functionality:'))
        self.stdout.write('=' * 40)
        
        # Test with RINV001
        try:
            invoice = RecurringInvoice.objects.get(reference_id='RINV001')
            renewal_info = invoice.get_renewal_info()
            
            self.stdout.write(f'Invoice: {invoice.reference_id}')
            self.stdout.write(f'End Date: {invoice.end_date}')
            self.stdout.write(f'Days Until Expiry: {renewal_info["days_until_expiry"]}')
            self.stdout.write(f'Needs Renewal: {renewal_info["needs_renewal"]}')
            self.stdout.write(f'Can Renew: {renewal_info["can_renew"]}')
            
            # Test renewal
            old_end_date = invoice.end_date
            success = invoice.renew_recurring_invoice()
            
            if success:
                self.stdout.write(self.style.SUCCESS('✅ Renewal test successful!'))
                self.stdout.write(f'  Old End Date: {old_end_date}')
                self.stdout.write(f'  New End Date: {invoice.end_date}')
            else:
                self.stdout.write(self.style.ERROR('❌ Renewal test failed'))
                
        except RecurringInvoice.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ RINV001 not found'))

    def show_help(self):
        self.stdout.write(self.style.SUCCESS('Recurring Invoice Renewal Management'))
        self.stdout.write('=' * 50)
        self.stdout.write('Available commands:')
        self.stdout.write('  --list     : List all invoices with renewal status')
        self.stdout.write('  --renew ID : Renew a specific invoice')
        self.stdout.write('  --test     : Test renewal functionality')
        self.stdout.write('')
        self.stdout.write('Examples:')
        self.stdout.write('  python manage.py recurring_renewal --list')
        self.stdout.write('  python manage.py recurring_renewal --renew RINV001')
        self.stdout.write('  python manage.py recurring_renewal --test')

