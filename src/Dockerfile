# Same version as the PI --> cat /etc/os-release
# https://hub.docker.com/r/arm64v8/python/
FROM arm64v8/python:bullseye

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Workdir
WORKDIR /projet

# Install system dependencies
RUN apt-get update
RUN apt-get -y install
# netcat gcc postgresql
RUN apt-get clean

# Install python requirements
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Install application
COPY . .

CMD [ "python3", "-m" , "python", "run", "--host=0.0.0.0"]
