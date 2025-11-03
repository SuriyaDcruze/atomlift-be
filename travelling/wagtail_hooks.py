from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse
from .models import TravelRequest
import json

# Travel Request SnippetViewSet
class TravelRequestViewSet(SnippetViewSet):
    model = TravelRequest
    menu_label = "Travel Requests"
    icon = "globe"
    menu_order = 200
    list_display = ('travel_date', 'from_place', 'to_place', 'travel_by', 'amount', 'created_by')
    list_filter = ('travel_date', 'travel_by', 'created_by')
    search_fields = ('from_place', 'to_place', 'created_by__username')

    def get_urlpatterns(self):
        urlpatterns = super().get_urlpatterns()
        return urlpatterns

# Travel Request Group
class TravelRequestGroup(SnippetViewSetGroup):
    items = (TravelRequestViewSet,)
    menu_icon = "globe"
    menu_label = "Travel Request"
    menu_name = "travel_request"
    menu_order = 12

# Register the Travel Request group
register_snippet(TravelRequestGroup)

# # Custom menu item for Travel Request frontend
# @hooks.register('register_admin_menu_item')
# def register_travel_request_menu_item():
#     return MenuItem(
#         'Travel Request',
#         reverse('travelling:travel_request_frontend'),
#         icon_name='globe',
#         order=10001
#     )
