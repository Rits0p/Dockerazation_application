import json, base64

code = """sequenceDiagram
autonumber

participant Browser as User's Browser
participant Server as Django Server
participant DB as SQLite Database

Note over Browser, DB: 1. Logging In (Issuing Dual JWTs)
Browser->>Server: POST /login/ (Username, Password)
Server->>DB: Query user by Username & Password
DB-->>Server: User Found! (user_id: 10)

alt Correct Credentials
    Server->>Server: Generate JWT access_token (15 mins)
    Server->>Server: Generate JWT refresh_token (7 days)
    Server-->>Browser: Redirect /home/ + [Set-Cookie: access_token & refresh_token]
else Incorrect Credentials
    Server-->>Browser: Return HTML Error Message
end

Note over Browser, Server: 2. Normal Flow (Access Token is Valid)
Browser->>Server: GET /employees/ + [Cookie: access_token & refresh_token]
Server->>Server: @custom_login_required Intercepts
Server->>Server: jwt.decode(access_token) -> Valid!
Server-->>Browser: Returns Protected HTML Page 

Note over Browser, Server: 3. Auto-Refresh (Access Token is EXPIRED)
Browser->>Server: GET /employees/ + [Cookies: access_token, refresh_token]
Server->>Server: @custom_login_required Intercepts
Server->>Server: jwt.decode(access_token) -> ExpiredSignatureError!
Server->>Server: jwt.decode(refresh_token) -> Valid!
Server->>Server: Automatically Generate NEW access_token 
Server-->>Browser: Return Page & [Set-Cookie: NEW access_token]

Note over Browser, Server: 4. Logging Out (Wipe JWTs)
Browser->>Server: GET /logout/
Server->>Server: Delete 'access_token' & 'refresh_token' cookies
Server-->>Browser: Redirect to /login/
"""

payload = {
    "code": code,
    "mermaid": {"theme": "default"}
}

json_str = json.dumps(payload)
base64_str = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
print("https://mermaid.ink/img/" + base64_str)
