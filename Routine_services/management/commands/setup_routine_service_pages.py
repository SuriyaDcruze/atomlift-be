"""
Management command to create routine service pages in Wagtail
"""
from django.core.management.base import BaseCommand
from wagtail.models import Page, Site
from Routine_services.models import (
    RoutineServicesIndexPage,
    AllRoutineServicesPage,
    TodayServicesPage,
    RouteWiseServicesPage,
    ThisMonthServicesPage,
    LastMonthOverduePage,
    ThisMonthOverduePage,
    ThisMonthCompletedPage,
    LastMonthCompletedPage,
    PendingServicesPage,
)


class Command(BaseCommand):
    help = 'Creates routine service pages in Wagtail if they do not exist'

    def handle(self, *args, **options):
        # Get the home page (root page for the site)
        try:
            site = Site.objects.get(is_default_site=True)
            home_page = site.root_page
        except Site.DoesNotExist:
            # Fallback to first root page
            home_page = Page.objects.filter(depth=2).first()
            if not home_page:
                self.stdout.write(self.style.ERROR('No home page found. Please create a site first.'))
                return

        # Check if Routine Services Index Page exists
        services_index = RoutineServicesIndexPage.objects.live().first()
        
        if not services_index:
            self.stdout.write('Creating Routine Services Index Page...')
            services_index = RoutineServicesIndexPage(
                title='Routine Services',
                slug='routine-services',
                show_in_menus=True
            )
            home_page.add_child(instance=services_index)
            services_index.save_revision().publish()
            self.stdout.write(self.style.SUCCESS('Created Routine Services Index Page'))
        else:
            self.stdout.write(self.style.WARNING(f'Routine Services Index Page already exists: {services_index.title}'))

        # Define service pages to create
        service_pages = [
            (AllRoutineServicesPage, 'All Routine Services', 'all-routine-services'),
            (TodayServicesPage, 'Today\'s Services', 'todays-services'),
            (RouteWiseServicesPage, 'Route Wise Services', 'route-wise-services'),
            (ThisMonthServicesPage, 'This Month Services', 'this-month-services'),
            (LastMonthOverduePage, 'Last Month Overdue', 'last-month-overdue'),
            (ThisMonthOverduePage, 'This Month Overdue', 'this-month-overdue'),
            (ThisMonthCompletedPage, 'This Month Completed', 'this-month-completed'),
            (LastMonthCompletedPage, 'Last Month Completed', 'last-month-completed'),
            (PendingServicesPage, 'Pending Services', 'pending-services'),
        ]

        # Create each service page if it doesn't exist
        for page_model, title, slug in service_pages:
            existing_page = page_model.objects.live().first()
            
            if not existing_page:
                self.stdout.write(f'Creating {title}...')
                new_page = page_model(
                    title=title,
                    slug=slug,
                    show_in_menus=True
                )
                services_index.add_child(instance=new_page)
                new_page.save_revision().publish()
                self.stdout.write(self.style.SUCCESS(f'Created {title}'))
            else:
                self.stdout.write(self.style.WARNING(f'{title} already exists'))

        self.stdout.write(self.style.SUCCESS('\nRoutine Service pages setup complete!'))
        self.stdout.write('The Routine Services menu should now appear in the Wagtail admin sidebar.')

