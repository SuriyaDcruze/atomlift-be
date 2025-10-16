from wagtail import hooks
from django.utils.html import format_html
from django.templatetags.static import static

@hooks.register("insert_editor_js")
def add_amc_autofill_js():
    # Inject our JavaScript file into Wagtail admin
    return format_html('<script src="{}"></script>', static("amc/js/amc_autofill.js"))
