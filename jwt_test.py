import jwt

token = jwt.encode({"user": "mansoor"}, "secret", algorithm="HS256")
print("Token:", token)

decoded = jwt.decode(token, "secret", algorithms=["HS256"])
print("Decoded:", decoded)
