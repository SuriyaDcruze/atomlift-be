from wagtail import hooks
from django.templatetags.static import static
from django.utils.html import format_html


@hooks.register("insert_editor_js")
def auto_calculate_load_kg_js():
    return format_html(
        '<script src="{}"></script>',
        static("lift/js/auto_load_kg.js")
    )
