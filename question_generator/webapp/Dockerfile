# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /usr/src/app
ADD ../requirements.txt requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy the current directory contents into the container at /usr/src/app
#COPY . .
#ADD data /tmp/data
#ADD src /tmp/src

# Make port 80 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
#CMD ["python", "/tmp/src/WebApp/app.py"]

# Define environment variable
ENV FLASK_APP=/tmp/src/app.py
ENV FLASK_ENV=development

# Command to run the Flask application
#CMD ["flask", "run", "--host=0.0.0.0", "--port=80", "--debug"]
CMD ["bash", "-c", "flask run --host=0.0.0.0 --port=80 --debug"]