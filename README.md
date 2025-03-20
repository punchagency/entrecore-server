# PUNCH-ENTRECORE

Enterprise Core Services Platform - A microservices-based backend infrastructure for scalable enterprise applications.

## Overview

PUNCH-ENTRECORE is a comprehensive backend platform designed to serve as a foundation for enterprise applications. Built with scalability, security, and maintainability in mind, it provides core services necessary for modern enterprise software.

The platform follows a microservices architecture, with each service handling a specific domain of functionality:

- **Auth Service**: Authentication and user management service
- **Entrecore Auth Core**: Shared authentication library used across services

## Repository Structure

```
punch-entrecore/
├── auth_service/            # Authentication service
├── entrecore_auth_core/     # Shared authentication library
├── architecture.md          # System architecture documentation
├── architecture_per_role.md # Role-specific architecture details
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Python 3.9+
- Poetry (dependency management)
- PostgreSQL
- Git

### Cloning the Repository

```bash
git clone https://github.com/punchagency/entrecore-server.git
cd entrecore-server
```

## Auth Service

The Authentication Service provides a complete authentication and user management solution for applications. It handles:

- User registration and management
- JWT-based authentication
- Role-based access control
- OAuth integration (Google)
- Password reset workflows
- Email verification

For detailed setup instructions and API documentation, see the [Auth Service README](auth_service/README.md).

## Entrecore Auth Core Library

The Entrecore Auth Core Library contains shared models and utilities for authentication that can be used across different services. This approach ensures consistency in how authentication is handled throughout the platform.

For information on the library features and usage examples, see the [Entrecore Auth Core README](entrecore_auth_core/README.md).

### Building and Installing the Library

To build the auth core library for local development:

```bash
# Navigate to the library directory
cd entrecore_auth_core

# Install dependencies and build the library
poetry install
poetry build

# To use the library in another service (e.g., auth_service)
cd ../auth_service
poetry remove entrecore-auth-core  # Remove existing version if any
poetry add ../entrecore_auth_core  # Add the local version
```

If you encounter issues with changes not being reflected, see the debugging section in the [Entrecore Auth Core README](entrecore_auth_core/README.md#debugging).

## Development Workflow

### Working with Multiple Services

When working on features that span multiple services:

1. Make changes to the shared libraries first (e.g., entrecore_auth_core)
2. Build the libraries following the instructions above
3. Update the services that use the libraries
4. Test the integration between services

### Testing

Each service includes its own test suite. Run the tests for each service individually:

```bash
# For auth service
cd auth_service
poetry run pytest

# For other services
# cd other_service
# poetry run pytest
```

## Architecture

For detailed information about the system architecture:
(Note that the Architecture is still in progress)

- [Overall Architecture](architecture.md) - System-wide architecture documentation
- [Role-Specific Architecture](architecture_per_role.md) - Architecture details specific to different roles

## Contributing

We welcome contributions to PUNCH-ENTRECORE! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows our coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.