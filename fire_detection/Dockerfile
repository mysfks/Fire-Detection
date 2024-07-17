# Use the official Node.js image as a base image
FROM node:14

# Set the working directory in the container to /app
WORKDIR /app

# Copy the package.json and package-lock.json files to the container
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code to the container
COPY . .

# Build the Vue.js application
RUN npm run build

# Expose port 8080 for the Vue.js app
EXPOSE 8080

# Start the Vue.js server
CMD ["npm", "run", "serve"]
