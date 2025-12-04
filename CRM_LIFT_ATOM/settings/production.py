from .base import *

DEBUG = False

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/5.1/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-aq^j733pcc(@0(g+^qcl_38flq_+((_bj3t&+nv)8^9h@rdbkd"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://*.technuob.com",
    "https://*.vercel.app/",
    "http://192.168.8.103:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost:8081",
    "https://admin.careelevators.in/",
    "https://technician.careelevators.in/",
]




try:
    from .local import *
except ImportError:
    pass
