from wagtail import hooks
from django import forms
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
import json

from .models import CustomUser
from wagtail.admin.menu import MenuItem


@hooks.register('register_admin_urls')
def register_add_user_custom_url():
    return [
        path('users/add-custom/', add_user_custom, name='add_user_custom'),
    ]


def add_user_custom(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            phone_number = data.get('phone_number', '').strip()
            password = data.get('password', '')

            if not email or not password:
                return JsonResponse({'success': False, 'error': 'Email and password are required.'}, status=400)

            # Create user
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
            )

            return JsonResponse({'success': True, 'message': 'User created successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return render(request, 'authentication/add_user_custom.html', {})


@hooks.register('construct_user_form')
def inject_phone_into_user_create(form_class, request):
    # Ensure our model has phone_number and the field isn't already included
    if hasattr(CustomUser, 'phone_number') and 'phone_number' not in getattr(form_class.Meta, 'fields', []):
        class PhoneUserCreateForm(form_class):
            phone_number = forms.CharField(required=False, max_length=15, label='Phone number')

            class Meta(form_class.Meta):
                fields = list(getattr(form_class.Meta, 'fields', ())) + ['phone_number']
        return PhoneUserCreateForm
    return form_class


@hooks.register('construct_user_edit_form')
def inject_phone_into_user_edit(form_class, request):
    if hasattr(CustomUser, 'phone_number') and 'phone_number' not in getattr(form_class.Meta, 'fields', []):
        class PhoneUserEditForm(form_class):
            phone_number = forms.CharField(required=False, max_length=15, label='Phone number')

            class Meta(form_class.Meta):
                fields = list(getattr(form_class.Meta, 'fields', ())) + ['phone_number']
        return PhoneUserEditForm
    return form_class



