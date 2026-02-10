"""Tests for profile CRUD endpoints."""

from unittest.mock import AsyncMock, patch

PROFILES_BASE = "/v1/profiles"


# ── GET /v1/profiles/me ─────────────────────────────────────────────


def test_get_profile_requires_auth(client):
    response = client.get(f"{PROFILES_BASE}/me")
    assert response.status_code == 401


def test_get_profile_returns_existing(client, auth_headers, test_user_id):
    profile_data = {
        "id": test_user_id,
        "username": "testuser",
        "full_name": "Test User",
        "avatar_url": None,
        "skill_level": "beginner",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    with patch(
        "app.api.endpoints.profiles.DatabaseOperations.get_profile",
        new_callable=AsyncMock,
        return_value=profile_data,
    ):
        response = client.get(f"{PROFILES_BASE}/me", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "testuser"
    assert body["id"] == test_user_id


def test_get_profile_auto_creates_when_missing(client, auth_headers, test_user_id):
    created_profile = {
        "id": test_user_id,
        "username": None,
        "full_name": None,
        "avatar_url": None,
        "skill_level": "beginner",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    with (
        patch(
            "app.api.endpoints.profiles.DatabaseOperations.get_profile",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.api.endpoints.profiles.DatabaseOperations.create_profile",
            new_callable=AsyncMock,
            return_value=created_profile,
        ) as mock_create,
    ):
        response = client.get(f"{PROFILES_BASE}/me", headers=auth_headers)

    assert response.status_code == 200
    mock_create.assert_awaited_once()
    body = response.json()
    assert body["id"] == test_user_id


# ── POST /v1/profiles/ ──────────────────────────────────────────────


def test_create_profile_requires_auth(client):
    response = client.post(f"{PROFILES_BASE}/", json={"username": "newuser"})
    assert response.status_code == 401


def test_create_profile_success(client, auth_headers, test_user_id):
    payload = {
        "username": "newuser",
        "full_name": "New User",
        "avatar_url": "https://example.com/avatar.png",
        "skill_level": "intermediate",
    }
    created_profile = {
        "id": test_user_id,
        **payload,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    with patch(
        "app.api.endpoints.profiles.DatabaseOperations.create_profile",
        new_callable=AsyncMock,
        return_value=created_profile,
    ):
        response = client.post(f"{PROFILES_BASE}/", json=payload, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "newuser"
    assert body["skill_level"] == "intermediate"


def test_create_profile_invalid_skill_level(client, auth_headers):
    payload = {
        "username": "newuser",
        "skill_level": "expert",  # not in beginner|intermediate|advanced
    }
    response = client.post(f"{PROFILES_BASE}/", json=payload, headers=auth_headers)
    assert response.status_code == 422


# ── PUT /v1/profiles/me ─────────────────────────────────────────────


def test_update_profile_requires_auth(client):
    response = client.put(f"{PROFILES_BASE}/me", json={"full_name": "Updated"})
    assert response.status_code == 401


def test_update_profile_success(client, auth_headers, test_user_id):
    updated_profile = {
        "id": test_user_id,
        "username": "testuser",
        "full_name": "Updated Name",
        "avatar_url": None,
        "skill_level": "advanced",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-06-01T00:00:00Z",
    }
    with patch(
        "app.api.endpoints.profiles.DatabaseOperations.update_profile",
        new_callable=AsyncMock,
        return_value=updated_profile,
    ):
        response = client.put(
            f"{PROFILES_BASE}/me",
            json={"full_name": "Updated Name", "skill_level": "advanced"},
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Updated Name"
    assert body["skill_level"] == "advanced"


def test_update_profile_no_fields(client, auth_headers):
    from app.core.exceptions import ValidationError

    with patch(
        "app.api.endpoints.profiles.DatabaseOperations.update_profile",
        new_callable=AsyncMock,
        side_effect=ValidationError("profile", "No valid fields to update"),
    ):
        response = client.put(f"{PROFILES_BASE}/me", json={}, headers=auth_headers)

    assert response.status_code == 400


def test_update_profile_rejects_extra_fields(client, auth_headers):
    response = client.put(
        f"{PROFILES_BASE}/me",
        json={"full_name": "Valid", "bogus_field": "rejected"},
        headers=auth_headers,
    )
    assert response.status_code == 422
