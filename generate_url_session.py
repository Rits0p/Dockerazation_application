import json, base64

code = """sequenceDiagram
autonumber

participant Browser as User's Browser
participant Server as Django Server
participant DB as SQLite Database

Note over Browser, DB: 1. Logging In (Session Creation)
Browser->>Server: POST /login/ (Username, Password)
Server->>DB: Query user by Username & Password
DB-->>Server: User Found! (user_id: 10)

alt Correct Credentials
    Server->>DB: INSERT INTO django_session (session_key, session_data)
    DB-->>Server: OK (session_key created, e.g. 'abc123xyz')
    Server-->>Browser: Redirect to /home/ + [Set-Cookie: sessionid=abc123xyz]
else Incorrect Credentials
    Server-->>Browser: Return HTML Error Message
end

Note over Browser, DB: 2. Accessing Protected Pages (Verification)
Browser->>Server: GET /employees/ + [Cookie: sessionid=abc123xyz]
Server->>Server: @custom_login_required Intercepts route
Server->>Server: Reads 'sessionid' cookie
Server->>DB: SELECT session_data WHERE session_key='abc123xyz'

alt Session Exists & Valid
    DB-->>Server: Returns session_data (contains {user_id: 10})
    Server-->>Browser: Returns Protected HTML Page 
else Session Not Found / Expired
    DB-->>Server: Empty Result
    Server-->>Browser: Redirect to /login/ 
end

Note over Browser, DB: 3. Logging Out (Session Destruction)
Browser->>Server: GET /logout/
Server->>Server: Reads 'sessionid' cookie
Server->>DB: DELETE FROM django_session WHERE session_key='abc123xyz'
Server-->>Browser: Redirect to /login/ + [Delete Cookie Command]
"""

payload = {
    "code": code,
    "mermaid": {"theme": "default"}
}

json_str = json.dumps(payload)
base64_str = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
print("https://mermaid.ink/img/" + base64_str)
