from wagtail.snippets.models import register_snippet
from .models import DeliveryChallanGroup

# DeliveryChallanGroup is now registered as part of SalesGroup in home/wagtail_hooks.py
# Do NOT register it here to avoid duplicate menu items
# register_snippet(DeliveryChallanGroup)



