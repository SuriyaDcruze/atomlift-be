from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)

        first_name = extra_fields.get("first_name", "")
        last_name = extra_fields.get("last_name", "")

        # Auto-generate username from first and last name if not provided
        username = extra_fields.get("username")
        if not username:
            base_username = (first_name + last_name).strip() or email.split("@")[0]
            username = base_username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

        extra_fields["username"] = username

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, editable=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full_name if full_name else self.email

    @property
    def full_name(self):
        """Used in Wagtail admin list display"""
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        Fallback to email if no name is provided.
        """
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full_name or self.email

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email
    
    def get_profile_phone(self):
        """Get phone number from profile"""
        if hasattr(self, 'profile') and self.profile:
            return self.profile.phone_number or self.phone_number or '-'
        return self.phone_number or '-'
    get_profile_phone.short_description = 'Phone Number'


class UserProfile(models.Model):
    """
    Extended profile for CustomUser to store additional information like phone number.
    This allows us to add more fields without modifying the core user model.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile', unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name='Phone Number')
    branch = models.CharField(max_length=100, blank=True, null=True, verbose_name='Branch')
    route = models.CharField(max_length=100, blank=True, null=True, verbose_name='Route')
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name='Code')
    designation = models.CharField(max_length=100, blank=True, null=True, verbose_name='Designation')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Profile"
    
    def clean(self):
        """Validate that we're not creating a duplicate profile"""
        from django.core.exceptions import ValidationError
        if not self.pk and UserProfile.objects.filter(user=self.user).exists():
            raise ValidationError({
                'user': 'A profile for this user already exists. Please edit the existing profile instead of creating a new one.'
            })
    
    def save(self, *args, **kwargs):
        """Call clean before saving"""
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# Signal to automatically create UserProfile when a CustomUser is created
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for every new user"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class OTP(models.Model):
    """
    Model to store OTP codes for mobile app authentication
    """
    OTP_TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=10, choices=OTP_TYPE_CHOICES)
    contact_info = models.CharField(max_length=255)  # email or phone number
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp_type}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only set expiry time for new OTPs
            self.expires_at = timezone.now() + timedelta(minutes=10)  # OTP expires in 10 minutes
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is valid (not used, not expired, and attempts < 3)"""
        return not self.is_used and not self.is_expired() and self.attempts < 3
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.save()
    
    def increment_attempts(self):
        """Increment failed attempts"""
        self.attempts += 1
        self.save()
    
    @classmethod
    def generate_otp(cls, user, otp_type, contact_info):
        """Generate a new OTP for user"""
        # Deactivate any existing OTPs for this user
        cls.objects.filter(user=user, otp_type=otp_type, is_used=False).update(is_used=True)
        
        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Create new OTP
        otp = cls.objects.create(
            user=user,
            otp_code=otp_code,
            otp_type=otp_type,
            contact_info=contact_info
        )
        
        return otp
    
    @classmethod
    def verify_otp(cls, user, otp_code, otp_type):
        """Verify OTP for user"""
        try:
            otp = cls.objects.get(
                user=user,
                otp_code=otp_code,
                otp_type=otp_type,
                is_used=False
            )
            
            if not otp.is_valid():
                otp.increment_attempts()
                return False, "OTP expired or maximum attempts exceeded"
            
            otp.mark_as_used()
            return True, "OTP verified successfully"
            
        except cls.DoesNotExist:
            return False, "Invalid OTP"
