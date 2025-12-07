FROM node:18-alpine

WORKDIR /app

# Build argument for API URL
ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Copy package files
COPY package.json package-lock.json* ./

# Install ALL dependencies (needed for react-scripts build)
RUN npm install && npm cache clean --force

# Copy application code
COPY . .

# Build application
RUN npm run build

# Install serve for production
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Serve the build
CMD ["serve", "-s", "build", "-l", "3000"]
