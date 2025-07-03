from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
import firebase_admin
from firebase_admin import auth, credentials
from django.contrib.auth import get_user_model
from django.conf import settings
import os

# Initialize Firebase App if it's not already initialized
if not firebase_admin._apps:
    # Build the full path to the service account key (relative to this file)
    cred_path = os.path.join(os.path.dirname(__file__), '../Firebase/serviceAccountKey.json')
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

# Get the custom user model (AUTH_USER_MODEL)
User = get_user_model()

# Custom authentication class for Firebase users
class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get the 'Authorization' header from the request
        auth_header = request.headers.get('Authorization')

        # If no header or it doesn't start with "Bearer ", don't authenticate
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        # Extract the Firebase ID token from the header
        id_token = auth_header.split(' ')[1]

        try:
            # Verify the token using Firebase Admin SDK
            decoded_token = auth.verify_id_token(id_token)
            email = decoded_token.get('email')  # Get user's email
            uid = decoded_token.get('uid')      # Get user's Firebase UID
        except Exception as e:
            # If verification fails, deny authentication
            raise exceptions.AuthenticationFailed(f'Invalid Firebase token: {str(e)}')

        # Get or create a Django user using the email from Firebase
        user, created = User.objects.get_or_create(email=email)

        # Return the authenticated user (2nd value is for auth token, which we don't need here)
        return (user, None)
