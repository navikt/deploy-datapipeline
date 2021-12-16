FROM python:3.9.1-buster

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd -ms /bin/bash 1069
COPY . .
EXPOSE 8080
CMD [ "python", "./app.py" ]