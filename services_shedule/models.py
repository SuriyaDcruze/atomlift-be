from django.db import models
from amc.models import AMC, AMCRoutineService
from django.utils.html import format_html
from django.utils import timezone

class RoutineServiceScheduleView(AMC):
    """
    Proxy model for displaying AMC Service Schedules in a specific tabular format.
    """
    class Meta:
        proxy = True
        verbose_name = "Routine Service Schedule"
        verbose_name_plural = "Routine Service Schedules"

    def site_name_display(self):
        return self.customer.site_name if self.customer else "—"
    site_name_display.short_description = "SITE NAME"
    site_name_display.admin_order_field = 'customer__site_name'

    def route_display(self):
        if self.customer:
            if hasattr(self.customer, 'city') and self.customer.city:
                return str(self.customer.city)
            if hasattr(self.customer, 'routes') and self.customer.routes:
                return str(self.customer.routes)
        return "—"
    route_display.short_description = "ROUTE"

    def amc_display(self):
        return self.reference_id
    amc_display.short_description = "AMC"
    amc_display.admin_order_field = 'reference_id'

    def contract_start_display(self):
        return self.start_date.strftime('%d-%m-%Y') if self.start_date else "—"
    contract_start_display.short_description = "CONTRACT START"
    contract_start_display.admin_order_field = 'start_date'

    def contract_end_display(self):
        return self.end_date.strftime('%d-%m-%Y') if self.end_date else "—"
    contract_end_display.short_description = "CONTRACT END"
    contract_end_display.admin_order_field = 'end_date'

    def contract_type_display(self):
        return str(self.amc_type) if self.amc_type else "—"
    contract_type_display.short_description = "CONTRACT TYPE"

    def _get_service_html(self, index):
        """Helper to generate HTML for the Nth service"""
        services = self.routine_services.all().order_by('service_date')
        if len(services) > index:
            service = services[index]
            date_str = service.service_date.strftime('%d/%m/%Y')
            status = service.status
            
            bg_color = ""
            text_color = "black"
            status_text = status
            
            if status == 'overdue':
                bg_color = "#cc0000" # Red
                text_color = "white"
            elif status == 'completed':
                bg_color = "#006400" # Dark Green
                text_color = "white"
            elif status == 'due':
                bg_color = "transparent"
            
            # Additional check for 'due' but date passed (if not auto-updated yet)
            if status == 'due' and service.service_date < timezone.now().date():
                 bg_color = "#cc0000"
                 text_color = "white"
                 status_text = "overdue"

            style = f"background-color: {bg_color}; color: {text_color}; padding: 10px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;"
            
            return format_html(
                '<div style="{}">'
                '<div style="font-weight: bold;">{}</div>'
                '<div>{}</div>'
                '</div>',
                style,
                date_str,
                status_text
            )
        return "—"

    def service_1(self):
        return self._get_service_html(0)
    service_1.short_description = "SERVICE 1"
    service_1.allow_tags = True

    def service_2(self):
        return self._get_service_html(1)
    service_2.short_description = "SERVICE 2"
    service_2.allow_tags = True

    def service_3(self):
        return self._get_service_html(2)
    service_3.short_description = "SERVICE 3"
    service_3.allow_tags = True

    def service_4(self):
        return self._get_service_html(3)
    service_4.short_description = "SERVICE 4"
    service_4.allow_tags = True

    def service_5(self):
        return self._get_service_html(4)
    service_5.short_description = "SERVICE 5"
    service_5.allow_tags = True

    def service_6(self):
        return self._get_service_html(5)
    service_6.short_description = "SERVICE 6"
    service_6.allow_tags = True

    def service_7(self):
        return self._get_service_html(6)
    service_7.short_description = "SERVICE 7"
    service_7.allow_tags = True

    def service_8(self):
        return self._get_service_html(7)
    service_8.short_description = "SERVICE 8"
    service_8.allow_tags = True

    def service_9(self):
        return self._get_service_html(8)
    service_9.short_description = "SERVICE 9"
    service_9.allow_tags = True

    def service_10(self):
        return self._get_service_html(9)
    service_10.short_description = "SERVICE 10"
    service_10.allow_tags = True

    def service_11(self):
        return self._get_service_html(10)
    service_11.short_description = "SERVICE 11"
    service_11.allow_tags = True

    def service_12(self):
        return self._get_service_html(11)
    service_12.short_description = "SERVICE 12"
    service_12.allow_tags = True

    def scheduled_services_count(self):
        return self.routine_services.count()
    scheduled_services_count.short_description = "TOTAL SERVICES"
