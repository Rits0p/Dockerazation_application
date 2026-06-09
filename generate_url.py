import json, base64

code = """sequenceDiagram
autonumber

participant Browser as User's Browser
participant Server as Django Server
participant DB as SQLite Database

Note over Browser, DB: 1. Logging In (Token Creation)
Browser->>Server: POST /login/ (Username, Password)
Server->>DB: Query user by Username & Password
DB-->>Server: User Found! (user_id: 10)

alt Correct Credentials
    Server->>Server: Serialize & Sign Data: signing.dumps({'user_id': 10})
    Server->>Server: Result: secure_token_string
    Server-->>Browser: Redirect to /home/ + [Set-Cookie: auth_token]
else Incorrect Credentials
    Server-->>Browser: Return HTML Error Message
end

Note over Browser, DB: 2. Accessing Protected Pages (Verification)
Browser->>Server: GET /employees/ + [Cookie: auth_token]
Server->>Server: @custom_login_required Intercepts route
Server->>Server: Reads 'auth_token' cookie

alt Token is Clean & Valid
    Server->>Server: Cryptographically decrypts token
    Server->>Server: Yields: {'user_id': 10}
    Server-->>Browser: Returns Protected HTML Page 
else Token is Tampered / Expired
    Server->>Server: Throws BadSignature Exception
    Server-->>Browser: Redirect to /login/ 
end

Note over Browser, DB: 3. Logging Out (Token Destruction)
Browser->>Server: GET /logout/
Server->>Server: response.delete_cookie('auth_token')
Server-->>Browser: Redirect to /login/ + [Delete Cookie Command]
"""

payload = {
    "code": code,
    "mermaid": {"theme": "default"}
}

json_str = json.dumps(payload)
base64_str = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
print("https://mermaid.ink/img/" + base64_str)
