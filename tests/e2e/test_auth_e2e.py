"""
Playwright E2E tests for authentication flows (registration and login).

These tests verify:
- Positive: Register with valid data, login with correct credentials
- Negative: Register with short password, login with wrong password

Uses pytest-playwright with a live FastAPI server.
"""
import re
import threading
import time
from uuid import uuid4

import pytest
import uvicorn
from playwright.sync_api import Page, expect

from app.api.main import app


class ServerThread(threading.Thread):
    """Background thread to run the FastAPI server for E2E tests."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server = None

    def run(self):
        config = uvicorn.Config(app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


@pytest.fixture(scope="module")
def server():
    """Start the FastAPI server in a background thread for the test module."""
    server_thread = ServerThread(port=8765)
    server_thread.start()
    # Wait for server to start
    time.sleep(1)
    yield f"http://{server_thread.host}:{server_thread.port}"
    server_thread.stop()


@pytest.fixture(scope="module")
def app_url(server):
    """Provide the app URL for tests."""
    return server


class TestRegistrationE2E:
    """E2E tests for user registration flow."""

    def test_register_with_valid_data_shows_success(self, page: Page, app_url: str):
        """
        Positive test: Register with valid email format, password length >= 6.
        Verify success message is displayed.
        """
        unique = uuid4().hex[:8]
        username = f"user_{unique}"
        email = f"{unique}@example.com"
        password = "securepass123"

        # Navigate to registration page
        page.goto(f"{app_url}/static/register.html")

        # Verify page loaded
        expect(page.locator("h1")).to_have_text("Create Account")

        # Fill in the form fields
        page.fill("#username", username)
        page.fill("#email", email)
        page.fill("#password", password)
        page.fill("#confirmPassword", password)

        # Submit the form
        page.click("#submitBtn")

        # Wait for and verify success message
        message_box = page.locator("#messageBox")
        expect(message_box).to_be_visible(timeout=5000)
        expect(message_box).to_have_class(re.compile(r"success-box"))
        expect(message_box).to_contain_text("Registration successful")

    def test_register_with_short_password_shows_error(self, page: Page, app_url: str):
        """
        Negative test: Register with password < 6 characters.
        Verify front-end validation shows error message.
        """
        unique = uuid4().hex[:8]
        username = f"user_{unique}"
        email = f"{unique}@example.com"
        short_password = "abc"  # Less than 6 characters

        # Navigate to registration page
        page.goto(f"{app_url}/static/register.html")

        # Fill in the form with short password
        page.fill("#username", username)
        page.fill("#email", email)
        page.fill("#password", short_password)
        page.fill("#confirmPassword", short_password)

        # Submit the form
        page.click("#submitBtn")

        # Verify password error message is shown (client-side validation)
        password_error = page.locator("#passwordError")
        expect(password_error).to_be_visible()
        expect(password_error).to_contain_text("at least 6 characters")

    def test_register_with_invalid_email_shows_error(self, page: Page, app_url: str):
        """
        Negative test: Register with invalid email format.
        Verify front-end validation shows error message.
        """
        unique = uuid4().hex[:8]
        username = f"user_{unique}"
        invalid_email = "not-an-email"
        password = "securepass123"

        # Navigate to registration page
        page.goto(f"{app_url}/static/register.html")

        # Fill in the form with invalid email
        page.fill("#username", username)
        page.fill("#email", invalid_email)
        page.fill("#password", password)
        page.fill("#confirmPassword", password)

        # Submit the form
        page.click("#submitBtn")

        # Verify email error message is shown
        email_error = page.locator("#emailError")
        expect(email_error).to_be_visible()
        expect(email_error).to_contain_text("valid email")

    def test_register_with_mismatched_passwords_shows_error(self, page: Page, app_url: str):
        """
        Negative test: Register with non-matching passwords.
        Verify front-end validation shows error message.
        """
        unique = uuid4().hex[:8]
        username = f"user_{unique}"
        email = f"{unique}@example.com"

        # Navigate to registration page
        page.goto(f"{app_url}/static/register.html")

        # Fill in the form with mismatched passwords
        page.fill("#username", username)
        page.fill("#email", email)
        page.fill("#password", "password123")
        page.fill("#confirmPassword", "different456")

        # Submit the form
        page.click("#submitBtn")

        # Verify confirm password error message is shown
        confirm_error = page.locator("#confirmPasswordError")
        expect(confirm_error).to_be_visible()
        expect(confirm_error).to_contain_text("do not match")


class TestLoginE2E:
    """E2E tests for user login flow."""

    def test_login_with_correct_credentials_shows_success(self, page: Page, app_url: str):
        """
        Positive test: Login with correct credentials.
        Verify success message and token is stored.
        """
        unique = uuid4().hex[:8]
        username = f"user_{unique}"
        email = f"{unique}@example.com"
        password = "securepass123"

        # First, register the user via API
        page.request.post(
            f"{app_url}/users/register",
            data={"username": username, "email": email, "password": password},
        )

        # Navigate to login page
        page.goto(f"{app_url}/static/login.html")

        # Verify page loaded
        expect(page.locator("h1")).to_have_text("Login")

        # Fill in the form fields
        page.fill("#email", email)
        page.fill("#password", password)

        # Submit the form
        page.click("#submitBtn")

        # Wait for and verify success message
        message_box = page.locator("#messageBox")
        expect(message_box).to_be_visible(timeout=5000)
        expect(message_box).to_have_class(re.compile(r"success-box"))
        expect(message_box).to_contain_text("Login successful")

        # Verify token is stored in localStorage
        token = page.evaluate("() => localStorage.getItem('access_token')")
        assert token is not None and len(token) > 0

    def test_login_with_wrong_password_shows_error(self, page: Page, app_url: str):
        """
        Negative test: Login with wrong password.
        Verify UI shows invalid credentials error message.
        """
        unique = uuid4().hex[:8]
        username = f"user_{unique}"
        email = f"{unique}@example.com"
        password = "securepass123"

        # First, register the user via API
        page.request.post(
            f"{app_url}/users/register",
            data={"username": username, "email": email, "password": password},
        )

        # Navigate to login page
        page.goto(f"{app_url}/static/login.html")

        # Fill in the form with wrong password
        page.fill("#email", email)
        page.fill("#password", "wrongpassword")

        # Submit the form
        page.click("#submitBtn")

        # Wait for and verify error message (server returns 401)
        message_box = page.locator("#messageBox")
        expect(message_box).to_be_visible(timeout=5000)
        expect(message_box).to_have_class(re.compile(r"error-box"))
        expect(message_box).to_contain_text("invalid credentials")

    def test_login_with_nonexistent_user_shows_error(self, page: Page, app_url: str):
        """
        Negative test: Login with email that doesn't exist.
        Verify UI shows invalid credentials error message.
        """
        # Navigate to login page
        page.goto(f"{app_url}/static/login.html")

        # Fill in the form with non-existent email
        page.fill("#email", "nonexistent@example.com")
        page.fill("#password", "somepassword")

        # Submit the form
        page.click("#submitBtn")

        # Wait for and verify error message
        message_box = page.locator("#messageBox")
        expect(message_box).to_be_visible(timeout=5000)
        expect(message_box).to_have_class(re.compile(r"error-box"))
        expect(message_box).to_contain_text("invalid credentials")

    def test_login_with_invalid_email_format_shows_client_error(self, page: Page, app_url: str):
        """
        Negative test: Login with invalid email format.
        Verify client-side validation shows error.
        """
        # Navigate to login page
        page.goto(f"{app_url}/static/login.html")

        # Fill in the form with invalid email format
        page.fill("#email", "not-an-email")
        page.fill("#password", "somepassword")

        # Submit the form
        page.click("#submitBtn")

        # Verify email error message is shown (client-side validation)
        email_error = page.locator("#emailError")
        expect(email_error).to_be_visible()
        expect(email_error).to_contain_text("valid email")

    def test_login_with_empty_password_shows_client_error(self, page: Page, app_url: str):
        """
        Negative test: Login with empty password.
        Verify client-side validation shows error.
        """
        # Navigate to login page
        page.goto(f"{app_url}/static/login.html")

        # Fill in email but leave password empty
        page.fill("#email", "test@example.com")
        # Don't fill password

        # Submit the form
        page.click("#submitBtn")

        # Verify password error message is shown
        password_error = page.locator("#passwordError")
        expect(password_error).to_be_visible()
        expect(password_error).to_contain_text("required")
