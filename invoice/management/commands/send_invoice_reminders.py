from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from datetime import timedelta
from invoice.models import Invoice, InvoiceReminder
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sends email reminders for invoices that are due soon, due today, or overdue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-before',
            type=int,
            default=3,
            help='Number of days before due date to send "due soon" reminder (default: 3)',
        )

    def handle(self, *args, **options):
        days_before = options['days_before']
        today = timezone.now().date()
        due_soon_date = today + timedelta(days=days_before)
        
        self.stdout.write('Sending invoice payment reminders...')
        
        sent_count = 0
        error_count = 0
        
        # 1. Send "due soon" reminders (3 days before due date)
        due_soon_invoices = Invoice.objects.filter(
            due_date=due_soon_date,
            status__in=['open', 'partially_paid']
        ).select_related('customer')
        
        for invoice in due_soon_invoices:
            if invoice.customer and invoice.customer.email:
                success = self.send_reminder_email(
                    invoice,
                    'due_soon',
                    f"Your invoice {invoice.reference_id} is due in {days_before} days"
                )
                if success:
                    sent_count += 1
                else:
                    error_count += 1
        
        # 2. Send "due today" reminders
        due_today_invoices = Invoice.objects.filter(
            due_date=today,
            status__in=['open', 'partially_paid']
        ).select_related('customer')
        
        for invoice in due_today_invoices:
            if invoice.customer and invoice.customer.email:
                success = self.send_reminder_email(
                    invoice,
                    'due_today',
                    f"Your invoice {invoice.reference_id} is due today"
                )
                if success:
                    sent_count += 1
                else:
                    error_count += 1
        
        # 3. Send "overdue" reminders (past due date)
        overdue_invoices = Invoice.objects.filter(
            due_date__lt=today,
            status__in=['open', 'partially_paid', 'due']
        ).select_related('customer')
        
        for invoice in overdue_invoices:
            if invoice.customer and invoice.customer.email:
                days_overdue = (today - invoice.due_date).days
                # Only send reminder if we haven't sent one in the last 7 days
                recent_reminder = InvoiceReminder.objects.filter(
                    invoice=invoice,
                    reminder_type='overdue',
                    reminder_date__gte=timezone.now() - timedelta(days=7)
                ).exists()
                
                if not recent_reminder:
                    success = self.send_reminder_email(
                        invoice,
                        'overdue',
                        f"Your invoice {invoice.reference_id} is {days_overdue} day(s) overdue"
                    )
                    if success:
                        sent_count += 1
                    else:
                        error_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully sent {sent_count} reminder(s). Errors: {error_count}'
            )
        )

    def send_reminder_email(self, invoice, reminder_type, subject_prefix):
        """Send reminder email for an invoice"""
        try:
            customer = invoice.customer
            if not customer or not customer.email:
                return False
            
            # Calculate amounts
            total_amount = invoice.get_total()
            days_until_due = (invoice.due_date - timezone.now().date()).days if invoice.due_date else 0
            days_overdue = (timezone.now().date() - invoice.due_date).days if invoice.due_date and invoice.due_date < timezone.now().date() else 0
            
            # Build email body
            if reminder_type == 'due_soon':
                urgency = f"Your invoice is due in {days_until_due} days."
            elif reminder_type == 'due_today':
                urgency = "Your invoice is due TODAY."
            else:
                urgency = f"Your invoice is {days_overdue} day(s) OVERDUE."
            
            email_body = f"""Dear {customer.site_name or 'Valued Customer'},

This is a friendly reminder regarding your invoice.

Invoice Details:
- Invoice Number: {invoice.reference_id}
- Invoice Date: {invoice.start_date.strftime('%d/%m/%Y') if invoice.start_date else 'N/A'}
- Due Date: {invoice.due_date.strftime('%d/%m/%Y') if invoice.due_date else 'N/A'}
- Amount Due: ₹{total_amount:.2f}
- Current Status: {invoice.get_status_display()}

{urgency}

Please make payment at your earliest convenience to avoid any service interruptions.

Payment Methods:
- Cash
- Cheque
- NEFT

If you have already made the payment, please ignore this reminder.

Thank you for your business.

Best regards,
Atom Lifts India Pvt Ltd
Phone: 9600087456
Email: admin@atomlifts.com
"""
            
            email = EmailMessage(
                subject=f'{subject_prefix} - Invoice {invoice.reference_id}',
                body=email_body,
                from_email=settings.EMAIL_HOST_USER,
                to=[customer.email],
            )
            email.send()
            
            # Record reminder
            InvoiceReminder.objects.create(
                invoice=invoice,
                reminder_type=reminder_type,
                sent_to_email=customer.email,
                sent_successfully=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending reminder for invoice {invoice.reference_id}: {str(e)}")
            
            # Record failed reminder
            try:
                InvoiceReminder.objects.create(
                    invoice=invoice,
                    reminder_type=reminder_type,
                    sent_to_email=customer.email if customer and customer.email else '',
                    sent_successfully=False,
                    error_message=str(e)
                )
            except:
                pass
            
            return False

