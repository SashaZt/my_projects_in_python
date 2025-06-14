import base64
password = "SashaZt83"
password_base64 = base64.b64encode(password.encode()).decode()
print(password_base64)
