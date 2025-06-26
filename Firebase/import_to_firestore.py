# 🔥 Firebase Admin SDK and JSON libraries
import firebase_admin
from firebase_admin import credentials, firestore
import json

# 🔐 Initialize Firebase using the service account key
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# 🧠 Get a Firestore database client
db = firestore.client()

# 👥 Upload users
def import_users():
    with open("users.json", "r") as f:
        users = json.load(f)
    
    for user in users:
        user["created_at"] = firestore.SERVER_TIMESTAMP
        db.collection("users").add(user)
        print(f"✅ Uploaded user: {user['full_name']}")

# 🚨 Upload emergency reports
def import_emergencies():
    with open("emergencies.json", "r") as f:
        emergencies = json.load(f)
    
    for emergency in emergencies:
        emergency["timestamp"] = firestore.SERVER_TIMESTAMP
        db.collection("emergencies").add(emergency)
        print(f"🔥 Emergency reported: {emergency['description']}")

# 🚑 Upload operator responses
def import_responses():
    with open("responses.json", "r") as f:
        responses = json.load(f)
    
    for response in responses:
        response["arrival_time"] = firestore.SERVER_TIMESTAMP
        db.collection("responses").add(response)
        print(f"🚨 Response by operator: {response['operator_email']}")

# 🚀 Run all import tasks
import_users()
import_emergencies()
import_responses()

print("\n🎉 All Firestore collections uploaded successfully!")
