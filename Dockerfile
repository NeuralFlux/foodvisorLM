# Set base image (host OS)
FROM python:3.9-slim-bookworm

# By default, listen on port 5000
EXPOSE 5000/tcp

# Set the working directory in the container
WORKDIR /app

# Install libs for barcode reader
RUN apt-get update
RUN apt-get install libzbar0 -y

# Copy the dependencies file to the working directory
ADD flask-app .

# Install Python dependencies
RUN pip install -r requirements.txt

# Specify the command to run on container start
CMD [ "python", "./app.py" ]