from django.db import models

# Create your models here.
from django.db import models
from django.forms.widgets import RadioSelect
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

# Import related models
from customer.models import Customer
from invoice.models import Invoice


# ---------- MAIN MODEL ----------
class PaymentReceived(models.Model):
    REFERENCE_PREFIX = 'PAY'

    payment_number = models.CharField(max_length=10, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Linked to a specific invoice for deposit consideration"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    payment_type = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Cash'),
            ('bank_transfer', 'Bank Transfer'),
        ],
        default='cash',
    )
    tax_deducted = models.CharField(
        max_length=20,
        choices=[
            ('no', 'No Tax deducted'),
            ('yes_tds', 'Yes, TDS (Income Tax)'),
        ],
        default='no',
    )
    uploads_files = models.FileField(
        upload_to='payment_received_uploads/',
        null=True,
        blank=True,
        max_length=100,
    )

    panels = [
        MultiFieldPanel([
            FieldPanel("payment_number", read_only=True),
            FieldPanel("customer"),
            FieldPanel("invoice"),
            FieldPanel("amount"),
            FieldPanel("date"),
        ], heading="Payment Details"),

        MultiFieldPanel([
            FieldPanel("payment_type", widget=RadioSelect),
            FieldPanel("tax_deducted", widget=RadioSelect),
        ], heading="Payment Type & Tax Deduction"),

        MultiFieldPanel([
            FieldPanel("uploads_files"),
        ], heading="Supporting Documents"),
    ]

    def save(self, *args, **kwargs):
        if not self.payment_number:
            last_payment = PaymentReceived.objects.all().order_by('id').last()
            if last_payment:
                try:
                    last_id = int(last_payment.payment_number.replace('PAY', ''))
                    next_id = last_id + 1
                except ValueError:
                    next_id = 1
                self.payment_number = f"{self.REFERENCE_PREFIX}{str(next_id).zfill(3)}"
            else:
                self.payment_number = f"{self.REFERENCE_PREFIX}001"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payment_number


# ---------- SNIPPET VIEWSET ----------
class PaymentReceivedViewSet(SnippetViewSet):
    model = PaymentReceived
    icon = "group"
    menu_label = "Payments Received"
    inspect_view_enabled = True
    list_display = ["payment_number", "customer", "invoice", "amount", "payment_type", "date"]
    list_export = [
        "payment_number", "customer", "invoice", "amount", "date",
        "payment_type", "tax_deducted"
    ]


# ---------- SNIPPET GROUP ----------
class PaymentGroup(SnippetViewSetGroup):
    items = (PaymentReceivedViewSet,)
    menu_icon = "group"
    menu_label = "Payment "
    menu_name = "payment"


# ---------- REGISTER GROUP ----------
register_snippet(PaymentGroup)
