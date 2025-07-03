from auth_utils import create_user, get_user_by_email

# Replace these with actual test values
email = "snow@gmail.com"
password = "123456"

# Test creating user
user = create_user(email, password)

# Test retrieving user by email
retrieved_user = get_user_by_email(email)
