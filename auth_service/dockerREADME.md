# Running with Docker

The auth service can be easily run using Docker and docker-compose for both development and production environments.

### Building and Running the Service

1. Build and start all services:
   ```bash
   docker-compose up
   ```

2. Run in detached mode (background):
   ```bash
   docker-compose up -d
   ```

3. View running containers:
   ```bash
   docker-compose ps
   ```

4. View logs:
   ```bash
   # All services
   docker-compose logs
   
   # Only the web service
   docker-compose logs web
   ```

5. Stop all services:
   ```bash
   docker-compose down
   ```

### After Making Code Changes

When you make changes to the code:

1. Rebuild and restart the service:
   ```bash
   docker-compose build web
   docker-compose up -d
   ```

2. Or rebuild and restart in one command:
   ```bash
   docker-compose up -d --build web
   ```

### Adding New Dependencies

When adding new dependencies to `pyproject.toml`:

1. Update local Poetry environment first:
   ```bash
   poetry update
   ```

2. Rebuild the Docker image to include new dependencies:
   ```bash
   docker-compose build web
   docker-compose up -d
   ```

### Running Tests in Docker

Execute tests within the Docker container to ensure they run in the same environment as the application:

1. Run all tests:
   ```bash
   docker-compose exec web pytest
   ```

2. Run specific test file:
   ```bash
   docker-compose exec web pytest tests/docker_test_auth_flow.py -v
   ```

3. Run tests with coverage report:
   ```bash
   docker-compose exec web pytest --cov=auth_service
   ```

- The `--no-cache` flag ensures a clean build to avoid any remnants of the previous incompatible packages.

```bash
docker-compose down
docker-compose build --no-cache web
docker-compose up
```

### Common Issues

- **Database connection errors**: Ensure the database container is running with `docker-compose ps`. Database initialization takes a few seconds.
- **Module import errors**: After adding new Python files, you may need to rebuild the image with `docker-compose build web`.
- **Permission issues**: If encountering permission problems with mounted volumes, check file ownership and permissions.