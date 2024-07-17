# Use an official Node.js runtime as a parent image
FROM node:14

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages
RUN npm install

# Expose port 8080 for the Vue.js app
EXPOSE 8080

# Start the Vue.js server
CMD ["npm", "run", "serve"]
