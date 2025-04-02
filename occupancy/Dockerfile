# Use the official Python image as a base
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the src folder
COPY src/ ./src

# Install Mosquitto MQTT broker
RUN apt-get update && apt-get install -y mosquitto mosquitto-clients && apt-get clean

# Copy Mosquitto configuration
COPY src/mosquitto.conf /etc/mosquitto/mosquitto.conf

# Expose MQTT broker port
EXPOSE 1883

# Start both the MQTT broker and your Python script
CMD ["sh", "-c", "mosquitto -c /etc/mosquitto/mosquitto.conf & python -u ./src/main.py"]
