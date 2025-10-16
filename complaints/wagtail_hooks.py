# complaints/wagtail_hooks.py
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail import hooks
from django.http import HttpResponse
from django.urls import path, reverse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from django.utils.html import format_html
from .models import Complaint
import logging

logger = logging.getLogger(__name__)


class ComplaintViewSet(SnippetViewSet):
    model = Complaint
    icon = "warning"
    menu_label = "Complaints"
    menu_order = 200
    add_to_admin_menu = True
    list_display = ["reference", "customer", "priority", "assign_to", "date", "download_pdf_link"]
    search_fields = ["reference", "customer__site_name"]

    # ✅ Add column with "Download PDF" link
    def download_pdf_link(self, instance):
        url = reverse("complaint_print", args=[instance.pk])
        return format_html('<a href="{}" class="button button-small">📄 Download PDF</a>', url)

    download_pdf_link.short_description = "Download"

    # ✅ PDF generation method
    def print_complaint(self, request, instance_id):
        try:
            complaint = Complaint.objects.select_related("customer", "assign_to").get(pk=instance_id)
        except Complaint.DoesNotExist:
            return HttpResponse("Complaint not found", status=404)

        # Prepare context
        context = {
            "company_name": "Atom Lifts India Pvt Ltd",
            "address": "No.87B, Pillayar Koll Street, Mannurpet, Ambattur Indus Estate, Chennai 50, CHENNAI",
            "phone": "9600087456",
            "email": "admin@atomlifts.com",
            "ticket_no": complaint.reference or "",
            "ticket_date": complaint.date.strftime("%d/%m/%Y %H:%M:%S") if complaint.date else "",
            "ticket_type": complaint.type or "",
            "priority": complaint.priority or "",
            "customer_name": getattr(complaint.customer, "site_name", "") if complaint.customer else "",
            "site_address": getattr(complaint.customer, "site_address", "") if complaint.customer else "",
            "contact_person": getattr(complaint.customer, "contact_person_name", "") or "",
            "contact_mobile": getattr(complaint.customer, "phone", "") or "",
            "block_wing": complaint.block_wing or "",
            "subject": complaint.subject or "",
            "message": complaint.message or "",
            "assigned_to": getattr(complaint.assign_to, "get_full_name", lambda: complaint.assign_to.username)()
            if complaint.assign_to else "Unassigned",
            "technician_remark": complaint.technician_remark or "",
            "solution": complaint.solution or "",
        }

        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Header
        header_style = ParagraphStyle(name="HeaderStyle", parent=styles["Heading1"], fontSize=18, alignment=1)
        story.append(Paragraph(context["company_name"], header_style))
        story.append(Paragraph(context["address"], styles["Normal"]))
        story.append(Paragraph(f"Phone: {context['phone']} | Email: {context['email']}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Ticket info
        table_data = [
            ["Ticket No:", context["ticket_no"]],
            ["Date:", context["ticket_date"]],
            ["Type:", context["ticket_type"]],
            ["Priority:", context["priority"]],
        ]
        t = Table(table_data, colWidths=[100, 400])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Customer info
        story.append(Paragraph("Customer Details", styles["Heading2"]))
        customer_data = [
            ["Customer Name:", context["customer_name"]],
            ["Site Address:", context["site_address"]],
            ["Contact Person:", context["contact_person"]],
            ["Contact Mobile:", context["contact_mobile"]],
            ["Block/Wing:", context["block_wing"]],
        ]
        ct = Table(customer_data, colWidths=[120, 380])
        ct.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)]))
        story.append(ct)
        story.append(Spacer(1, 12))

        # Complaint
        story.append(Paragraph("Complaint Details", styles["Heading2"]))
        story.append(Paragraph(f"Subject: {context['subject']}", styles["Normal"]))
        story.append(Paragraph(f"Message: {context['message']}", styles["Normal"]))
        story.append(Paragraph(f"Assigned To: {context['assigned_to']}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Resolution
        story.append(Paragraph("Resolution", styles["Heading2"]))
        story.append(Paragraph(f"Technician Remark: {context['technician_remark']}", styles["Normal"]))
        story.append(Paragraph(f"Solution: {context['solution']}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename=complaint_{context["ticket_no"]}.pdf'
        return response

    # ✅ Register custom route
    def get_admin_urls_for_registration(self):
        urls = super().get_admin_urls_for_registration()
        custom = [
            path("<int:instance_id>/print/", self.print_complaint, name="complaint_print"),
        ]
        return custom + urls


@hooks.register("register_snippet_viewset")
def register_complaint_viewset():
    return ComplaintViewSet()
