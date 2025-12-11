# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (required for some python packages like Pillow/Matplotlib)
# We also install Node.js here because the app orchestrates it
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    tk \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install Node.js dependencies
WORKDIR /app/whatsapp-service
RUN npm install

# Return to root
WORKDIR /app

# Create .env from example if not exists (User should mount .env)
# COPY .env.example .env

# Expose port for Node.js service
EXPOSE 3000

# Run the headless script (assuming user wants to run the CLI bot or a daemon)
# Since desktop_app.py is GUI, we can't run it easily.
# We'll default to a shell or a placeholder command.
CMD ["python", "stock-intelligence/main.py", "--help"]
