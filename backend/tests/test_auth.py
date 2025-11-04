"""
Tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_user():
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    assert "email" in response.json()


def test_register_duplicate_email():
    """Test registration with duplicate email."""
    # First registration
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    
    # Second registration with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 400


def test_login_success():
    """Test successful login."""
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    
    # Login
    form_data = {
        "username": "login@example.com",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/login", data=form_data)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    form_data = {
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", data=form_data)
    assert response.status_code == 401

