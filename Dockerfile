# Use an official Python image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy dependencies file first for better caching
COPY requirements.txt .

# Install necessary system dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .
COPY firebase-key.json .


# Expose port 8080 for Cloud Run
EXPOSE 8080

# Run FastAPI with Uvicorn (Use 2 workers for better performance)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"] 
