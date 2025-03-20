# Auth Service

Authentication microservice for the Entrecore platform, providing secure user management, authentication, and token handling for enterprise applications.

## Overview

This service handles all authentication concerns for the Entrecore ecosystem, including:

- User registration and management
- JWT-based authentication
- Role-based access control
- OAuth integration (Google)
- Password reset workflows
- Email verification
- Token management and revocation

## Features

- **Multi-step Registration**: Secure two-step user signup process
- **JWT Authentication**: Secure token generation and validation
- **OAuth Integration**: Sign in with Google
- **Password Management**: Secure reset and update flows
- **User Profiles**: User data management with proper validation
- **Role-based Access Control**: Granular permissions system
- **Token Blacklisting**: Ability to invalidate tokens for logout
- **Email Verification**: Workflow for verifying user email addresses

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Poetry (dependency management)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/punchagency/entrecore-server.git
   cd auth_service
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables (copy from example):
   ```bash
   cp .env.example .env
   # Edit the .env file with your configuration
   ```

4. Run database migrations:
   ```bash
   poetry run alembic upgrade head
   ```

5. Start the service:
   ```bash
   poetry run uvicorn auth_service.main:app --reload
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | localhost |
| `DB_PORT` | PostgreSQL port | 5432 |
| `DB_NAME` | Database name | entrecore_auth |
| `DB_USER` | Database username | postgres |
| `DB_PASSWORD` | Database password | password |
| `JWT_SECRET_KEY` | Secret for JWT tokens | (required) |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | 7 |

## API Endpoints

### Authentication

- `POST /token` - Obtain access tokens
- `POST /refresh-token` - Refresh access token
- `POST /logout` - Invalidate current token

### User Management

- `POST /signup` - Step 1 of user registration
- `POST /signup/set-password` - Step 2 of user registration
- `POST /signup/google` - Register or login with Google
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile

### Password Management

- `POST /password-reset/request` - Request password reset
- `POST /password-reset/confirm` - Confirm password reset

### Email Verification

- `POST /verify-email/{token}` - Verify email address

## Database Migrations with Alembic

### Initial Setup

1. Install Alembic using Poetry:
```bash
poetry add alembic
```

2. Initialize Alembic:
```bash
poetry run alembic init migrations
```

3. Configure `alembic.ini`:
```ini
# Update sqlalchemy.url
sqlalchemy.url = postgresql://%(DB_USER)s:%(DB_PASSWORD)s@%(DB_HOST)s:%(DB_PORT)s/%(DB_NAME)s
```

4. Update `migrations/env.py`:
```python
# Add these imports
from auth_service.database import Base
from auth_service import models
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Update config section
config.set_main_option("sqlalchemy.url", 
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Add this line to include your models
target_metadata = Base.metadata
```

### Working with Migrations

1. Create a new migration:
```bash
# Generate migration with a message
poetry run alembic revision --autogenerate -m "describe your changes"
```

2. Apply migrations:
```bash
# Apply all pending migrations
poetry run alembic upgrade head

# Apply specific migration
poetry run alembic upgrade <revision_id>

# Rollback one migration
poetry run alembic downgrade -1

# Rollback to specific migration
poetry run alembic downgrade <revision_id>
```

3. Check migration status:
```bash
# View current migration state
poetry run alembic current

# View migration history
poetry run alembic history
```

## Testing

Run the test suite with:

```bash
poetry run pytest
```

Run specific tests with:

```bash
poetry run pytest tests/test_auth_flow.py -v
```

## Docker Deployment

### Building the Docker Image

```bash
# From the auth_service directory
docker build -t auth-service:latest .

# Or from the project root
docker build -t auth-service:latest ./auth_service
```

### Running with Docker Compose

```bash
docker-compose up -d
```

This will start the service along with a PostgreSQL database. Access the API at http://localhost:8000 and the interactive documentation at http://localhost:8000/docs.

## Security Considerations

The auth service implements several security best practices:

- Password hashing with bcrypt
- JWT token management with proper expiration
- Token blacklisting for revocation
- Role-based access control
- Protection against brute force attacks
- Separation of access and refresh tokens

## For Production Environments

For production deployment, consider implementing:

- **OAuth/OIDC Integration**: Enable login with Azure AD, Google Workspace, etc.
- **Multi-Factor Authentication**: Implement TOTP or SMS verification
- **Password Policies**: Enforce strength requirements and expiration
- **Account Lockout**: Protect against brute force attacks
- **Audit Logging**: Track authentication events
- **Rate Limiting**: Prevent abuse of authentication endpoints
- **Redis for Token Storage**: Replace in-memory blacklist with Redis
- **HTTPS**: Ensure all traffic is encrypted

## License

This project is licensed under the MIT License - see the LICENSE file for details.