FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry==2.0.0

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy only the files needed for dependency installation
COPY pyproject.toml poetry.lock* README.md ./

# Copy the stub or poetry install will fail
COPY impresso_content_auth/__init__.py /app/impresso_content_auth/__init__.py

# Install dependencies
RUN poetry install --without dev

# Copy the application code
COPY impresso_content_auth /app/impresso_content_auth

# Set user
RUN adduser --disabled-password --no-create-home appuser
USER appuser

# Expose the port
EXPOSE 8000

# Run the server
CMD ["python", "-m", "impresso_content_auth.main", "--server"]
