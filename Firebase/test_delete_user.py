# test_delete_user.py
"""
Interactive script to delete a Firebase user by UID or email.
Uses delete_user() from auth_utils.py, and prompts for confirmation.
"""

from auth_utils import delete_user

def main():
    #  Script header
    print(" Firebase User Deletion Tool\n")

    #  Prompt the user to enter either a UID or an email
    identifier = input("Enter user UID or email to delete: ").strip()
    if not identifier:
        print("  No identifier provided. Exiting.")
        return

    #  Ask for explicit confirmation before performing deletion
    confirm = input(
        f"  Are you sure you want to delete user '{identifier}'? (yes/no): "
    ).strip().lower()

    #  If confirmed, call the centralized delete_user() function
    if confirm in ['yes', 'y']:
        success = delete_user(identifier)
        if success:
            print("  Deletion completed.")
        else:
            print("  Deletion failed. Check identifier and try again.")
    else:
        #  If not confirmed, abort without calling delete_user()
        print("  Deletion canceled by user.")

if __name__ == "__main__":
    main()
