from django.apps import AppConfig
import firebase_admin
from firebase_admin import credentials
from django.conf import settings


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        """
        This method is called automatically when the Django application starts.
        It's the perfect and safe place for one-time initialization code.
        """
        # Import here to avoid potential circular imports
        # from . import signals  # (if you had signals, you'd import them here too)

        # Initialize Firebase
        try:
            if not firebase_admin._apps: # Check if already initialized
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
                firebase_admin.initialize_app(cred)
                print("Firebase Admin SDK initialized successfully.")
        except ValueError as e:
            # This likely means it's already initialized, so we can ignore
            print(f"Firebase initialization note: {e}")
        except Exception as e:
            # Catch any other errors (e.g., file not found, invalid JSON)
            print(f"!!! ERROR: Failed to initialize Firebase Admin SDK: {e} !!!")
            # You might want to raise this or log it to Sentry in production
