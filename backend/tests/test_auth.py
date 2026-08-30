def test_signup_creates_user(client):
    response = client.post("/signup", json={
        "name": "Yash",
        "email": "yash@example.com",
        "password": "strongpass123",
    })

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "yash@example.com"
    assert data["role"] == 3
    assert "password" not in data  # response_model must never leak the hash


def test_signup_rejects_duplicate_email(client):
    client.post("/signup", json={
        "name": "Yash",
        "email": "yash@example.com",
        "password": "strongpass123",
    })

    response = client.post("/signup", json={
        "name": "Someone Else",
        "email": "yash@example.com",
        "password": "anotherpass123",
    })

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_succeeds_with_correct_password(client):
    client.post("/signup", json={
        "name": "Yash",
        "email": "yash@example.com",
        "password": "strongpass123",
    })

    response = client.post("/login", data={
        "username": "yash@example.com",
        "password": "strongpass123",
    })

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_fails_with_wrong_password(client):
    client.post("/signup", json={
        "name": "Yash",
        "email": "yash@example.com",
        "password": "strongpass123",
    })

    response = client.post("/login", data={
        "username": "yash@example.com",
        "password": "wrongpassword",
    })

    assert response.status_code == 401  