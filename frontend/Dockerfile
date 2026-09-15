FROM node:18-alpine

WORKDIR /var/www/outreach

# Copy package files
COPY package*.json .

# Install dependencies
RUN npm install

# Copy application
COPY . .

# Build for production
RUN npm run build

# Install serve to serve static files
RUN npm install -g serve

# Expose port
EXPOSE 80

# Serve built files
CMD ["serve", "-s", "dist", "-l", "80"]
