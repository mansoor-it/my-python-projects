from flask import Flask, request, jsonify, make_response
import jwt
import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# مفتاح التشفير (يجب أن يكون سريًا)
SECRET_KEY = "your_secret_key"

# بيانات المستخدم للتسجيل (في تطبيق حقيقي، يتم استخدام قاعدة بيانات)
USER_DATA = {"username": "testuser", "password": "password123"}


# وظيفة إنشاء JWT Token
def generate_token(username, token_type="access"):
    expiration = datetime.datetime.utcnow() + (
        datetime.timedelta(minutes=15) if token_type == "access" else datetime.timedelta(days=7)
    )
    payload = {
        "username": username,
        "type": token_type,
        "exp": expiration
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# تسجيل الدخول وإصدار Tokens
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == USER_DATA["username"] and password == USER_DATA["password"]:
        access_token = generate_token(username, "access")
        refresh_token = generate_token(username, "refresh")

        response = make_response(jsonify({"access_token": access_token}))
        response.set_cookie("refresh_token", refresh_token, httponly=True)
        return response
    return jsonify({"error": "Invalid credentials"}), 401



# الوصول إلى الموارد المحمية
@app.route("/protected", methods=["GET"])
def protected():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token is missing"}), 401

    try:
        # التحقق من صلاحية Access Token
        token_data = jwt.decode(token.split()[1], SECRET_KEY, algorithms=["HS256"])
        if token_data["type"] != "access":
            raise jwt.InvalidTokenError()
        return jsonify({"message": f"Welcome, {token_data['username']}!"})
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401


# تجديد Access Token باستخدام Refresh Token
@app.route("/refresh", methods=["POST"])
def refresh():
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return jsonify({"error": "Refresh token is missing"}), 401

    try:
        # التحقق من صلاحية Refresh Token
        token_data = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])
        if token_data["type"] != "refresh":
            raise jwt.InvalidTokenError()

        # إصدار Access Token جديد
        new_access_token = generate_token(token_data["username"], "access")
        return jsonify({"access_token": new_access_token})
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid refresh token"}), 401


if __name__ == "__main__":
    app.run(debug=False)
