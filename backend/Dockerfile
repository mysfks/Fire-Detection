# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 and 5001 for the Flask app
EXPOSE 5000 5001

# Start the Flask server
CMD ["sh", "-c", "python video_processing.py & python fire_detection.py"]
