# frontend/Dockerfile

# Base image
FROM node:16

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy project files
COPY . .

# Build the application
RUN npm run build

# Install serve to serve the application
RUN npm install -g serve

# Expose port
EXPOSE 5000

# Command to run the application
CMD ["serve", "-s", "dist"]
