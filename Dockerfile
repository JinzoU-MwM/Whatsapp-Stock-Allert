# Base Image: Python 3.9 (Slim)
FROM python:3.9-slim

# Install system dependencies & Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    supervisor \
    # Chrome dependencies for Puppeteer
    chromium \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Set Working Directory
WORKDIR /app

# Copy Project Files
COPY . .

# Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install streamlit

# Install Node.js Dependencies
WORKDIR /app/whatsapp-service
RUN npm install

# Puppeteer Config to use installed Chromium (Lighter than downloading Chrome)
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Reset Workdir
WORKDIR /app

# Expose Ports (Streamlit: 8080)
EXPOSE 8080

# Command to run Supervisor (Manages both Node & Python)
CMD ["/usr/bin/supervisord", "-c", "supervisord.conf"]
