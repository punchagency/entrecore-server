# entrecore-auth-core

[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![CodeQL](https://github.com/[YOUR_USERNAME]/entrecore-auth-core/workflows/CodeQL/badge.svg)](https://github.com/[YOUR_USERNAME]/entrecore-auth-core/actions?query=workflow%3ACodeQL)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A secure authentication core library for Python applications.

## Installation

```bash
pip install entrecore-auth-core
```

## Features

- User management with role-based access control
- JWT token handling and validation
- Secure token payload management
- Built-in timestamp handling with UTC
- UUID-based identifiers for users and tokens

## Secure Usage

### User Management

```python
from entrecore_auth_core.auth_models import User

user = User(email="test@example.com", username="testuser", full_name="Test User",roles=["user"])
```

### Token Management

```python
from entrecore_auth_core.auth_models import Token, TokenPayload
from datetime import datetime, timedelta, UTC

# Create a token payload
payload = TokenPayload(
sub=user.id,
exp=datetime.now(UTC) + timedelta(hours=1),
roles=user.roles
)

# Create a token
token = Token(
access_token="your_jwt_token_here",
expires_at=payload.exp,
refresh_token="your_refresh_token_here"
)
```

## Security Considerations

1. Always validate user input
2. Use HTTPS for all API communications
3. Implement proper rate limiting
4. Store tokens securely
5. Use environment variables for sensitive configurations
6. Implement proper token expiration and rotation
7. Regularly update dependencies

## Development

This project uses Poetry for dependency management. To get started:

```bash
# Install poetry
pip install poetry

# Install dependencies
poetry install

# Run tests
poetry run pytest
```

## Debugging

- If a change is made to the package and it is not reflecting in the auth_service, you can do the following:

```bash
# Build the package
poetry build

# Navigate to the auth_service directory
cd ../auth_service

# Uninstall the existing package
poetry remove entrecore-auth-core

# Reinstall the package with the latest changes
poetry add ../entrecore_auth_core
```

## Documentation

For detailed documentation on all features and security best practices, please visit our [documentation page](docs/).

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

## Security

For security-related issues, please read our [Security Policy](SECURITY.md) before reporting any vulnerabilities.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Create an issue for bug reports or feature requests
- Read our documentation for guides and API reference
- Follow security best practices outlined in our security policy

## Acknowledgments

- Built with [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- Uses Python's built-in UUID and datetime modules for secure ID generation and timestamp handling



