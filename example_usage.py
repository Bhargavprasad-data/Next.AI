"""
Example usage of the AI Application API
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def register_user(email: str, username: str, password: str):
    """Register a new user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "username": username, "password": password}
    )
    return response.json()


def login(email: str, password: str):
    """Login and get token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        params={"email": email, "password": password}
    )
    return response.json()


def get_current_user(token: str):
    """Get current user info"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    return response.json()


def send_message(message: str, token: str, context_id: str = None):
    """Send a message to the AI"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}
    if context_id:
        data["context_id"] = context_id
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers,
        json=data
    )
    return response.json()


def get_chat_history(token: str, limit: int = 50):
    """Get chat history"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/chat/history",
        headers=headers,
        params={"limit": limit}
    )
    return response.json()


def main():
    """Example usage"""
    print("AI Application API Example\n")
    
    # Register user
    print("1. Registering user...")
    user_data = register_user("test@example.com", "testuser", "testpass123")
    print(f"User registered: {user_data}")
    
    # Login
    print("\n2. Logging in...")
    auth_data = login("test@example.com", "testpass123")
    token = auth_data["access_token"]
    print(f"Login successful! Token: {token[:20]}...")
    
    # Get current user
    print("\n3. Getting current user info...")
    user_info = get_current_user(token)
    print(f"Current user: {user_info}")
    
    # Send messages
    print("\n4. Sending messages...")
    
    # First message
    response1 = send_message("What is machine learning?", token)
    print(f"\nUser: What is machine learning?")
    print(f"AI: {response1['response']}")
    
    # Second message with context
    response2 = send_message(
        "Can you give me more details?",
        token,
        context_id=response1["context_id"]
    )
    print(f"\nUser: Can you give me more details?")
    print(f"AI: {response2['response']}")
    
    # Get chat history
    print("\n5. Getting chat history...")
    history = get_chat_history(token)
    print(f"Chat history: {len(history.get('messages', []))} messages")
    
    print("\nExample complete!")


if __name__ == "__main__":
    main()


