import requests

url = "http://127.0.0.1:5000/login"
data = {
    "username": "testuser",
    "password": "password123"
}

response = requests.post(url, data=data)
print(response.json())
