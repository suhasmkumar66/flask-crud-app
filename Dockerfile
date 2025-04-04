# Use official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy files to the container
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 5000

# Command to run the app
CMD ["python", "app.py"]
