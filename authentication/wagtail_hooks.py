from wagtail import hooks
from wagtail.users.views.users import UserViewSet
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    model = User
    list_display = ["full_name", "email", "is_active", "is_staff"]
    list_filter = ["is_active", "is_staff"]
    search_fields = ["first_name", "last_name", "email"]

    # Optional: rename columns for clarity
    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        # Change header labels
        self.list_display_labels = {
            "full_name": "Full Name",
            "email": "Email",
            "is_active": "Active",
            "is_staff": "Staff",
        }
        return list_display


@hooks.register("register_admin_viewset")
def register_custom_user_viewset():
    return CustomUserViewSet("users", url_prefix="users")
