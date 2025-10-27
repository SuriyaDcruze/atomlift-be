from wagtail import hooks
from django import forms
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
import json

from .models import CustomUser, UserProfile
from wagtail.admin.menu import MenuItem
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register


# Hook to display success message after login
@receiver(user_logged_in)
def login_success_message(sender, request, user, **kwargs):
    """Add a success message when user logs in"""
    # Only show message for Wagtail admin logins
    if '/admin/' in request.path or request.session.get('_auth_user_backend'):
        # Clear any existing messages first
        storage = messages.get_messages(request)
        storage.used = True
        # Add the login success message
        messages.success(request, 'You have been successfully logged in.', extra_tags='login-success')


@hooks.register('register_admin_urls')
def register_add_user_custom_url():
    return [
        path('users/add-custom/', add_user_custom, name='add_user_custom'),
        path('api/user-phones/', get_user_phones, name='get_user_phones'),
    ]


def get_user_phones(request):
    """API endpoint to get phone numbers for all users"""
    users = CustomUser.objects.all().select_related('profile')
    phone_data = {}
    for user in users:
        phone = '-'
        if hasattr(user, 'profile') and user.profile and user.profile.phone_number:
            phone = user.profile.phone_number
        elif user.phone_number:
            phone = user.phone_number
        phone_data[str(user.pk)] = phone
    return JsonResponse(phone_data)


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
    # Removed phone number field from user create form
    return form_class


@hooks.register('construct_user_edit_form')
def inject_phone_into_user_edit(form_class, request):
    # Removed phone number field from user edit form
    return form_class


# Custom form for UserProfile to make user field read-only
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user', 'phone_number', 'branch', 'route', 'code', 'designation']
        widgets = {
            'user': forms.Select(attrs={'disabled': 'disabled'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make user field read-only if editing existing profile
        if self.instance and self.instance.pk:
            self.fields['user'].disabled = True
            self.fields['user'].required = False


# Register UserProfile in Wagtail Admin
class UserProfileAdmin(ModelAdmin):
    model = UserProfile
    menu_label = "User Profiles"
    menu_icon = "user"
    menu_order = 201
    add_to_settings_menu = True  # Add to Settings menu
    exclude_from_explorer = False
    list_display = ("user", "phone_number", "branch", "route", "code", "designation", "get_email")
    list_filter = []  # No filters
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name", "phone_number", "branch", "route", "code", "designation")
    list_display_add_buttons = None  # Remove the add button from list view
    list_per_page = 20  # Pagination
    
    # Disable the ability to create new profiles manually
    # Profiles are created automatically via signals
    def get_permission_helper_class(self):
        """Override permission helper to disable 'add' permission"""
        from wagtail_modeladmin.helpers import PermissionHelper
        
        class UserProfilePermissionHelper(PermissionHelper):
            def user_can_create(self, user):
                """Disable manual profile creation - profiles are auto-created via signals"""
                return False
        
        return UserProfilePermissionHelper
    
    def get_email(self, obj):
        """Display user email in the list"""
        return obj.user.email
    get_email.short_description = "Email"
    
    def get_full_name(self, obj):
        """Display user full name in the list"""
        return obj.user.get_full_name()
    get_full_name.short_description = "Full Name"
    
    def create_view(self, request):
        """Override create view to prevent manual profile creation"""
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.urls import reverse
        
        messages.error(
            request, 
            "User Profiles cannot be created manually. They are automatically created when a new user is added. "
            "Please edit an existing profile or create a new user."
        )
        # Redirect back to the list view
        return redirect(self.url_helper.index_url)


modeladmin_register(UserProfileAdmin)


# Inject JavaScript to auto-hide messages after a few seconds
@hooks.register('insert_global_admin_js')
def auto_hide_messages():
    """Add JavaScript to automatically hide success messages after 5 seconds"""
    return format_html(
        """
        <script>
        // Auto-hide messages after 5 seconds
        document.addEventListener('DOMContentLoaded', function() {{
            var messages = document.querySelectorAll('.messages .success, .messages .info, .messages .warning');
            messages.forEach(function(message) {{
                // Auto-hide after 5 seconds
                setTimeout(function() {{
                    if (message && message.parentNode) {{
                        message.style.transition = 'opacity 0.5s ease-out';
                        message.style.opacity = '0';
                        setTimeout(function() {{
                            if (message && message.parentNode) {{
                                message.remove();
                            }}
                        }}, 500);
                    }}
                }}, 5000);
                
                // Add close button functionality if it exists
                var closeBtn = message.querySelector('.close, .message-close, button');
                if (closeBtn) {{
                    closeBtn.addEventListener('click', function() {{
                        if (message && message.parentNode) {{
                            message.style.transition = 'opacity 0.5s ease-out';
                            message.style.opacity = '0';
                            setTimeout(function() {{
                                if (message && message.parentNode) {{
                                    message.remove();
                                }}
                            }}, 500);
                        }}
                    }});
                }}
            }});
        }});
        </script>
        <style>
        /* Style for login success messages */
        .messages .success {{
            animation: slideIn 0.3s ease-out;
        }}
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        </style>
        """
    )


# Removed phone number column from user listing
# The phone number column will no longer appear in the users table
