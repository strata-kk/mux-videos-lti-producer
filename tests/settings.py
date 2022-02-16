import os

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "lti_toolbox",
    "ltiproducer",
    "muxltiproducer",
]

SECRET_KEY = "dummy"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(os.path.dirname(__file__), "db.sqlite3"),
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MUX_TOKEN_ID = "dummy"
MUX_TOKEN_SECRET = "dummy"
MUX_SIGNING_KEY_ID = "dummy"
MUX_SIGNING_PRIVATE_KEY = "dummy"
MUX_WEBHOOK_SIGNING_SECRET = "dummy"
