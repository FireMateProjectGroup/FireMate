import firebase_admin
from firebase_admin import credentials, auth
import os

# Path to the service account key JSON file
SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')

# Initialize Firebase App if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)

def create_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        print('Successfully created new user:', user.uid)
        return user
    except Exception as e:
        print('Error creating new user:', e)
        return None

def get_user_by_email(email):
    try:
        user = auth.get_user_by_email(email)
        print('User found:', user.uid)
        return user
    except Exception as e:
        print('Error fetching user:', e)
        return None
