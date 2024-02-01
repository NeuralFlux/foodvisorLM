# Set base image (host OS)
FROM python:3.9-slim-bookworm

# By default, listen on port 5000
EXPOSE 5000/tcp

# Set the working directory in the container
WORKDIR /app

# Install libs for barcode reader
RUN apt-get update
RUN apt-get install libzbar0 -y

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the dependencies file to the working directory
ADD flask-app .

# Add environment variables
ARG OPENAI_API_KEY
ARG AUTH_ENDPOINT
ARG AUTH_CLIENT_ID
ARG API_ENDPOINT
ARG OPENSEARCH_USER
ARG OPENSEARCH_PWD

# Specify the command to run on container start
CMD [ "python", "./app.py" ]