from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-aq^j733pcc(@0(g+^qcl_38flq_+((_bj3t&+nv)8^9h@rdbkd"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CSRF_TRUSTED_ORIGINS = [
    "https://*.technuob.com",
    "https://*.vercel.app/",
    "http://192.168.8.103:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
try:
    from .local import *
except ImportError:
    pass
