from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse
from .models import MaterialRequest
import json

# Material Request SnippetViewSet
class MaterialRequestViewSet(SnippetViewSet):
    model = MaterialRequest
    menu_label = "Material Requests"
    icon = "form"
    menu_order = 100
    list_display = ('date', 'name', 'item', 'requested_by', 'added_by')
    list_filter = ('date', 'item', 'requested_by')
    search_fields = ('name', 'description', 'item', 'requested_by')

    def get_urlpatterns(self):
        urlpatterns = super().get_urlpatterns()
        return urlpatterns

# Material Request Group
class MaterialRequestGroup(SnippetViewSetGroup):
    items = (MaterialRequestViewSet,)
    menu_icon = "form"
    menu_label = "Material Request"
    menu_name = "material_request"
    menu_order = 11

# Register the Material Request group
register_snippet(MaterialRequestGroup)

# # Custom menu item for Material Request frontend
# @hooks.register('register_admin_menu_item')
# def register_material_request_menu_item():
#     return MenuItem(
#         'Material Request',
#         reverse('material_request:material_request_frontend'),
#         icon_name='form',
#         order=10000
#     )
