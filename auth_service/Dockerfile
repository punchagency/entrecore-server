FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock* /app/

# Install pip and critical dependencies explicitly to ensure they're in PATH
RUN pip install --upgrade pip && \
    pip install poetry==2.1.1 && \
    pip install fastapi uvicorn[standard] python-jose[cryptography] passlib[bcrypt] python-multipart

# Copy the rest of the application
COPY . /app/

# Install all dependencies via Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --without dev

# Verify critical packages are installed
RUN pip show python-jose && pip show fastapi && pip show uvicorn

# Expose port
EXPOSE 8000

# Define environment variable for Python to know about the installed packages
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "8000"]