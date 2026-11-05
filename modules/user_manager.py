import json
import os
import hashlib

USERS_FILE = "data/users.json"

def load_users():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = hash_password(password)
    save_users(users)
    return True, "Account created successfully!"

def login(username, password):
    users = load_users()
    if username in users and users[username] == hash_password(password):
        return True, "Login successful!"
    return False, "Invalid username or password."