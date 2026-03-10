import httpx

r = httpx.post("http://localhost:8000/api/v1/auth/login", json={"username": "admin", "password": "admin123456"})
print(f"Login status: {r.status_code}")
data = r.json()
token = data.get("access_token", "")
print(f"Token: {token[:40]}...")

r2 = httpx.get("http://localhost:8000/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
print(f"Me status: {r2.status_code}")
print(f"Me: {r2.json()}")
