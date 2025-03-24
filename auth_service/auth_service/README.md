# From the auth_service directory
docker build -t auth-service:latest .

# Or from the project root
docker build -t auth-service:latest ./auth_service

## Authentication Service Overview

Since this is targeting enterprise users who need to access ERP data, the authentication service needs to be robust, secure, and integrate well with the rest of the microservice ecosystem.

### Key Components
- User authentication (login/logout)
- Token management (JWT or similar) 
- Integration with identity providers
- Role-based access control
- Security features (MFA, password policies)
- Session management
- API endpoints for auth operations
- Integration with the API Gateway

Given the enterprise nature, we need a comprehensive solution that can handle SSO, enterprise identity, and security requirements.

┌─────────────────────────────────────────────────────────────┐
│                Authentication Service                       │
│                                                             │
│  ┌─────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Auth API Layer  │  │ Token Service  │  │ User Service │  │
│  └─────────────────┘  └────────────────┘  └──────────────┘  │
│                                                             │
│  ┌─────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ RBAC Provider   │  │ OAuth Provider │  │ Audit Logger │  │
│  └─────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘

### Enterprise-Grade Enhancements
For production, add these features:

- **OAuth/OIDC Integration**: Allow login with Azure AD, Google Workspace
- **Multi-Factor Authentication**: Implement TOTP or SMS verification  
- **Password Policies**: Enforce strength requirements and expiration
- **Account Lockout**: Protect against brute force attacks
- **Audit Logging**: Track authentication events

# Auth Service

Authentication microservice for the Entrecore platform.

## Development

### Requirements
- Python 3.9+
- Poetry
- Docker (#TODO: Add docker-compose file)

### Setup

1. You should have a postgresql@14 database instance running.

- You should also have alembic installed to manage the database migrations, navigate to `alembic.md` for more information.

2. Navigate to the `auth_service` sub-directory and run the following command:

    ```bash
    poetry run alembic upgrade head
    ```

3. Run the following command in the `auth_service` sub-directory, (i.e this directory) to start the service:

    ```bash
    poetry run uvicorn main:app --reload

### Using Docker 

Please refer to the [README.md](/dockerREADME.md) in the root directory for instructions on running the service with Docker.

4. Access the API at http://localhost:8000

5. #TODO: API documentation available at http://localhost:8000/docs