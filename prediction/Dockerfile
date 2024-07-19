# Use the official Python image
FROM python:3.8

# Set the working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["python", "fire_detection.py"]
