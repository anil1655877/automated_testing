# Use the official Microsoft Playwright Node.js image
FROM mcr.microsoft.com/playwright:v1.42.1-jammy

# Create app directory
WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install app dependencies
RUN npm install

# Copy application source code
COPY . .

# Expose HTTP / Socket.IO port
EXPOSE 5000

# Set environment defaults
ENV PORT=5000
ENV NODE_ENV=production

# Run the server
CMD [ "npm", "start" ]
