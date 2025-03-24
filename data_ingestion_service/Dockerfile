FROM python:3.11-slim

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create a non-root user and switch to it
RUN useradd -m appuser
USER appuser

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application
CMD ["uvicorn", "ingestion_service.main:app", "--host", "0.0.0.0", "--port", "8001"] 