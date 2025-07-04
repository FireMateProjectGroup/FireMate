#create user by reeferring to central auth logic
from auth_utils import create_user

#prompt for email and password
email= input("Enter email for new user:  ")
password= input("Enter password for new user: ")
#create user
create_user(email, pasword)