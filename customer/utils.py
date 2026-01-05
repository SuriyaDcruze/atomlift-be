"""
Utility functions for customer-related operations
"""
from .models import Customer


def resolve_customer_from_email(email):
    """
    Resolve a Customer object from an email address.
    Checks both Customer and SubCustomer models.
    
    Args:
        email: Email address to look up
        
    Returns:
        tuple: (customer_object, is_subcustomer_boolean) or (None, False) if not found
        
    Raises:
        Customer.DoesNotExist: If neither customer nor sub-customer found
    """
    # First, try to find customer by email
    try:
        customer = Customer.objects.get(email=email)
        return customer, False
    except Customer.DoesNotExist:
        pass
    
    # Check if this email belongs to a sub-customer
    try:
        from subcustomers.models import SubCustomer
        subcustomer = SubCustomer.objects.get(email=email, is_active=True)
        
        # Check if sub-customer has access permission
        if not subcustomer.can_access_app:
            raise Customer.DoesNotExist(
                f"Sub-customer with email {email} does not have permission to access the app"
            )
        
        # Return the parent customer
        return subcustomer.customer, True
        
    except ImportError:
        # SubCustomer model not available
        raise Customer.DoesNotExist(f"No customer found with email {email}")
    except Exception:
        # SubCustomer not found or other error
        raise Customer.DoesNotExist(f"No customer or sub-customer found with email {email}")



