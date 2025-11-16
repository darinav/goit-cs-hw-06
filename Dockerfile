FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY front-init/ ./front-init/

# Expose ports
EXPOSE 3000 5001

# Run the application
CMD ["python", "main.py"]

