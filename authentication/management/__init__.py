from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from authentication.models import OTP

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup mobile authentication system and create test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-groups',
            action='store_true',
            help='Create default employee groups',
        )
        parser.add_argument(
            '--create-test-user',
            action='store_true',
            help='Create a test user for mobile app',
        )
        parser.add_argument(
            '--cleanup-otps',
            action='store_true',
            help='Clean up expired and used OTPs',
        )

    def handle(self, *args, **options):
        if options['create_groups']:
            self.create_groups()
        
        if options['create_test_user']:
            self.create_test_user()
        
        if options['cleanup_otps']:
            self.cleanup_otps()

    def create_groups(self):
        """Create default employee groups"""
        groups = [
            'Employees',
            'Managers',
            'Technicians',
            'Field Staff',
            'Admin Staff'
        ]
        
        created_count = 0
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created group: {group_name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} new groups')
        )

    def create_test_user(self):
        """Create a test user for mobile app testing"""
        email = 'mobile.test@example.com'
        
        try:
            user = User.objects.get(email=email)
            self.stdout.write(
                self.style.WARNING(f'Test user {email} already exists')
            )
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                first_name='Mobile',
                last_name='Test',
                phone_number='+1234567890'
            )
            
            # Add to Employees group
            try:
                employee_group = Group.objects.get(name='Employees')
                user.groups.add(employee_group)
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('Employees group not found. Run with --create-groups first.')
                )
                return
            
            # Update profile
            user.profile.branch = 'Test Branch'
            user.profile.designation = 'Test Employee'
            user.profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Created test user: {email}')
            )
            self.stdout.write(
                self.style.SUCCESS('Password: Use OTP login for mobile app')
            )

    def cleanup_otps(self):
        """Clean up expired and used OTPs"""
        from django.utils import timezone
        
        # Delete expired OTPs
        expired_count = OTP.objects.filter(expires_at__lt=timezone.now()).count()
        OTP.objects.filter(expires_at__lt=timezone.now()).delete()
        
        # Delete used OTPs older than 1 day
        from datetime import timedelta
        old_used_count = OTP.objects.filter(
            is_used=True,
            created_at__lt=timezone.now() - timedelta(days=1)
        ).count()
        OTP.objects.filter(
            is_used=True,
            created_at__lt=timezone.now() - timedelta(days=1)
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Cleaned up {expired_count} expired OTPs')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Cleaned up {old_used_count} old used OTPs')
        )
