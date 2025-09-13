#!/usr/bin/env python3
"""Demo script for OAuth2 web interface functionality."""

import requests  # type: ignore

# Base URL for the API
BASE_URL = "http://localhost:8000"


def demo_oauth2_functionality():
    """Demonstrate OAuth2 token management functionality."""

    print("=== OAuth2 Token Management Demo ===\n")

    # Step 1: Register a user
    print("1. Registering a test user...")
    register_data = {
        "username": "oauth_demo_user",
        "email": "oauth_demo@example.com",
        "password": "DemoPass123!",  # pragma: allowlist secret
    }

    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 201:
        print("[OK] User registered successfully")
    else:
        print(f"[ERROR] Registration failed: {response.text}")
        return

    # Step 2: Login to get authentication token
    print("\n2. Logging in...")
    login_data = {
        "username": "oauth_demo_user",
        "password": "DemoPass123!",  # pragma: allowlist secret
    }

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        print("[OK] Login successful")
    else:
        print(f"[ERROR] Login failed: {response.text}")
        return

    # Set up headers for authenticated requests
    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 3: Create OAuth2 tokens for different services
    print("\n3. Creating OAuth2 tokens...")

    # GitHub token
    github_token = {
        "service_name": "github",
        "access_token": "gho_demo_github_token_123456789",
        "refresh_token": "ghr_demo_github_refresh_123456789",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "read-only",
        "client_id": "demo_github_client",
    }

    response = requests.post(
        f"{BASE_URL}/oauth/tokens", json=github_token, headers=headers
    )
    if response.status_code == 201:
        print("[OK] GitHub token created successfully")
    else:
        print(f"[ERROR] GitHub token creation failed: {response.text}")

    # Google token
    google_token = {
        "service_name": "google",
        "access_token": "ya29_demo_google_token_123456789",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "profile",
        "client_id": "demo_google_client",
    }

    response = requests.post(
        f"{BASE_URL}/oauth/tokens", json=google_token, headers=headers
    )
    if response.status_code == 201:
        print("[OK] Google token created successfully")
    else:
        print(f"[ERROR] Google token creation failed: {response.text}")

    # Step 4: List all tokens
    print("\n4. Listing all OAuth2 tokens...")
    response = requests.get(f"{BASE_URL}/oauth/tokens", headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        print(f"Found {len(tokens)} tokens: ")
        for token in tokens:
            print(
                f"  - {token['service_name']}: {token['scope']} "
                f"(expires: {token.get('expires_at', 'Never')})"
            )
    else:
        print(f"[ERROR] Failed to list tokens: {response.text}")

    # Step 5: Get a specific token
    print("\n5. Retrieving GitHub token...")
    response = requests.get(
        f"{BASE_URL}/oauth/tokens/github", headers=headers
    )
    if response.status_code == 200:
        token = response.json()
        print(f"[OK] GitHub token retrieved: {token['scope']} scope")
    else:
        print(f"[ERROR] Failed to retrieve GitHub token: {response.text}")

    # Step 6: Get decrypted token (for API use)
    print("\n6. Getting decrypted GitHub token...")
    response = requests.get(
        f"{BASE_URL}/oauth/tokens/github/decrypted", headers=headers
    )
    if response.status_code == 200:
        token_data = response.json()
        print(f"[OK] Decrypted token: {token_data['access_token'][:20]}...")
        print(f"  Service: {token_data['service_name']}")
        print(f"  Retrieved at: {token_data['retrieved_at']}")
    else:
        print(f"[ERROR] Failed to get decrypted token: {response.text}")

    # Step 7: Test password entry verification
    print("\n7. Testing password entry verification...")
    password_data = {
        "password": "DemoPass123!",  # pragma: allowlist secret
        "service_name": "github",
        "remember_me": False,
    }

    response = requests.post(
        f"{BASE_URL}/oauth/password-entry",
        data=password_data,
        headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        print("[OK] Password verification successful")
        print(f"  Service: {result['service_name']}")
        print(f"  Tokens count: {result['tokens_count']}")
        print(f"  Scopes: {', '.join(result['scopes'])}")
    else:
        print(f"[ERROR] Password verification failed: {response.text}")

    # Step 8: Get available services and scopes
    print("\n8. Getting available services and scopes...")

    response = requests.get(f"{BASE_URL}/oauth/services", headers=headers)
    if response.status_code == 200:
        services = response.json()
        services_list = ", ".join([s["name"] for s in services])
        print(f"[OK] Available services: {services_list}")
    else:
        print(f"[ERROR] Failed to get services: {response.text}")

    response = requests.get(f"{BASE_URL}/oauth/scopes", headers=headers)
    if response.status_code == 200:
        scopes = response.json()
        print(f"[OK] Available scopes: {', '.join(scopes.keys())}")
    else:
        print(f"[ERROR] Failed to get scopes: {response.text}")

    # Step 9: Test web interface endpoints
    print("\n9. Testing web interface endpoints...")

    web_endpoints = ["/oauth/", "/oauth/add-token", "/oauth/password-entry"]

    for endpoint in web_endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        if (
            response.status_code == 200
            and "text/html" in response.headers.get(
                "content-type", ""
            )
        ):
            print(f"[OK] {endpoint} - Web interface accessible")
        else:
            print(
                f"[ERROR] {endpoint} - Web interface failed: "
                f"{response.status_code}"
            )

    # Step 10: Cleanup - revoke a token
    print("\n10. Revoking Google token...")
    response = requests.delete(
        f"{BASE_URL}/oauth/tokens/google", headers=headers
    )
    if response.status_code == 200:
        print("[OK] Google token revoked successfully")
    else:
        print(f"[ERROR] Failed to revoke Google token: {response.text}")

    print("\n=== Demo completed! ===")
    print("\nTo access the web interface:")
    print("1. Start the server: uvicorn app.main:app --reload")
    print("2. Open browser: http://localhost:8000/oauth/")
    print(
        "3. Login with username: oauth_demo_user, "
        "password: DemoPass123!"  # pragma: allowlist secret
    )  # pragma: allowlist secret


if __name__ == "__main__":
    try:
        demo_oauth2_functionality()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print(
            "Please make sure the server is running on "
            "http://localhost:8000"
        )
        print("Start it with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"Error: {e}")
