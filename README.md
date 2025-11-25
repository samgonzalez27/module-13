# FastAPI Calculator with JWT Authentication

A FastAPI-based calculator application with JWT authentication, PostgreSQL database, and Docker Compose stack.

## Docker Hub

**Image:** [samgonzalezalberto/module-13](https://hub.docker.com/r/samgonzalezalberto/module-13)

```bash
docker pull samgonzalezalberto/module-13:latest
docker run -p 8000:8000 samgonzalezalberto/module-13:latest
```

## Features

- **JWT Authentication** – Secure user registration and login with JSON Web Tokens
- **Calculator API** – RESTful endpoints for arithmetic operations
- **Web Frontend** – HTML/CSS/JavaScript interface for auth and calculator
- **PostgreSQL** – Persistent storage for users and calculations
- **100% Test Coverage** – Unit, integration, and Playwright E2E tests
- **CI/CD** – GitHub Actions with automated testing and Docker Hub deployment

---

## Quick Start

```bash
# Start the full stack (app + PostgreSQL + pgAdmin)
docker compose up --build -d
```

| Service      | URL                        |
| ------------ | -------------------------- |
| **App**      | http://localhost:8000      |
| **pgAdmin**  | http://localhost:5050      |
| **API Docs** | http://localhost:8000/docs |

```bash
# Stop the stack
docker compose down

# Stop and remove volumes (deletes DB data)
docker compose down -v
```

---

## Frontend Pages

| Page       | URL                                 | Description                      |
| ---------- | ----------------------------------- | -------------------------------- |
| Calculator | http://localhost:8000/              | Main calculator with auth status |
| Register   | http://localhost:8000/register.html | User registration form           |
| Login      | http://localhost:8000/login.html    | User login form                  |

### Frontend Features

- **Registration**: Username, email, password with client-side validation (email format, min 6-char password, confirmation match). JWT stored in localStorage on success.
- **Login**: Email/password authentication with error handling. JWT stored on success.
- **Calculator**: Shows logged-in status, logout button, navigation to auth pages.

---

## Running Tests

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Unit & Integration Tests

```bash
# Run all tests
pytest -q

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

### Playwright E2E Tests

```bash
# Install Playwright
pip install pytest-playwright
playwright install chromium

# Run E2E tests
pytest tests/e2e/test_auth_e2e.py -v
```

#### E2E Test Coverage

| Test                                  | Description                           |
| ------------------------------------- | ------------------------------------- |
| `test_registration_page_loads`        | Registration page loads correctly     |
| `test_successful_registration`        | Complete registration with valid data |
| `test_registration_password_mismatch` | Password confirmation validation      |
| `test_registration_invalid_email`     | Email format validation               |
| `test_login_page_loads`               | Login page loads correctly            |
| `test_successful_login`               | Login with valid credentials          |
| `test_login_invalid_credentials`      | Error handling for wrong password     |
| `test_login_nonexistent_user`         | Error handling for non-existent email |
| `test_login_empty_fields`             | Form validation for empty fields      |

### PostgreSQL Integration Tests

```bash
# Start Postgres container
docker run --name calc-postgres -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=test_db -p 5432:5432 -d postgres:15

# Run integration tests
DATABASE_URL=postgresql://test:test@localhost:5432/test_db pytest -q tests/integration
```

---

## Environment Variables

| Variable       | Description                              |
| -------------- | ---------------------------------------- |
| `DATABASE_URL` | PostgreSQL connection string             |
| `SECRET_KEY`   | JWT signing key (use strong key in prod) |

Keep `.env` out of version control. Use `.env.example` as a template.

---

## API Examples

```bash
# Register a user
curl -X POST http://localhost:8000/users/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123"}'

# Login (returns JWT)
curl -X POST http://localhost:8000/users/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com","password":"secret123"}'

# Use protected endpoint
TOKEN="<your-jwt-token>"
curl -X POST http://localhost:8000/calculations \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"a":3,"b":4,"type":"add"}'
```

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`):

1. Runs unit and integration tests with PostgreSQL service
2. Runs Playwright E2E tests
3. Builds and pushes Docker image to Docker Hub (on `main` branch)

### Required GitHub Secrets

| Secret               | Description             |
| -------------------- | ----------------------- |
| `DOCKERHUB_USERNAME` | Docker Hub username     |
| `DOCKERHUB_TOKEN`    | Docker Hub access token |

---

## Submission Checklist

- **GitHub Repository:** [https://github.com/samgonzalez27/module-13](https://github.com/samgonzalez27/module-13)
- **Docker Hub:** [https://hub.docker.com/r/samgonzalezalberto/module-13](https://hub.docker.com/r/samgonzalezalberto/module-13)

**Required Screenshots:**
1. GitHub Actions showing successful workflow run
2. Docker Hub showing the pushed image tag

---

## License

This project is for educational purposes.
