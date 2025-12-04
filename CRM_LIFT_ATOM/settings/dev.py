# from .base import *

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

# # SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = "django-insecure-aq^j733pcc(@0(g+^qcl_38flq_+((_bj3t&+nv)8^9h@rdbkd"

# # SECURITY WARNING: define the correct hosts in production!
# ALLOWED_HOSTS = ["*"]


# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = "atom.lift.1@gmail.com"
# EMAIL_HOST_PASSWORD = "rldeunwqzvkmltnv"

# CSRF_TRUSTED_ORIGINS = [
#     "https://*.technuob.com",
#     "https://*.vercel.app/",
#     "http://192.168.8.103:8000",
#     "http://127.0.0.1:8000",
#     "http://localhost:8000",
#     "http://localhost:8081",
#     "https://admin.careelevators.in/",
#     "https://technician.careelevators.in/",
# ]

# # Note: CSRF middleware is enabled for Wagtail admin security
# # Mobile API endpoints are exempted using @csrf_exempt decorator
# try:
#     from .local import *
# except ImportError:
#     pass

from .base import *  # import base settings (keeps other settings)



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



# -- Database: override to use RDS MySQL --
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "atomliftdb",
        "USER": "dbadmin",
        "PASSWORD": "Atom$1234",
        "HOST": "atomliftprod.c9iu6ua48ejv.ap-south-1.rds.amazonaws.com",
        "PORT": "3306",
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
