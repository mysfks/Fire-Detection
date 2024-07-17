# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 and 5001
EXPOSE 5000
EXPOSE 5001

# Start the backend servers
CMD ["sh", "-c", "python fire_detection.py & python video_processing.py"]
