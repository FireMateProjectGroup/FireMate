import firebase_admin
from firebase_admin import credentials, auth
import os

# Path to the service account key JSON file
SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')

# Initialize Firebase App if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)

#  Create a new user
def create_user(email, password):
    """
    Creates a new Firebase user.
    """
    try:
        user = auth.create_user(email=email, password=password)
        print(' Successfully created new user:', user.uid)
        return user
    except Exception as e:
        print(' Error creating user:', e)
        return None

#  Fetch a user by email
def get_user_by_email(email):
    """
    Fetches a Firebase user by their email.
    """
    try:
        user = auth.get_user_by_email(email)
        print(' User found:', user.uid)
        return user
    except Exception as e:
        print(' Error fetching user:', e)
        return None

#  Delete a user (by email or UID)
def delete_user(identifier):
    """
    Deletes a Firebase user by UID or email.
    """
    try:
        # If it's an email, fetch the UID first
        uid = identifier
        if "@" in identifier:
            user = auth.get_user_by_email(identifier)
            uid = user.uid
        auth.delete_user(uid)
        print(f" Successfully deleted user with UID: {uid}")
        return True
    except auth.UserNotFoundError:
        print(" User not found.")
    except Exception as e:
        print(" Error deleting user:", e)
    return False

#  Update user data
def update_user(uid, email=None, password=None, display_name=None):
    """
    Updates user attributes like email, password, or display name.
    """
    try:
        user = auth.update_user(
            uid,
            email=email,
            password=password,
            display_name=display_name,
        )
        print(f" Successfully updated user: {user.uid}")
        return user
    except Exception as e:
        print(" Error updating user:", e)
        return None
