FROM python:3.10.1-buster

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN curl https://sh.rustup.rs -sSfy | sh
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd --system --gid 1069 apprunner
RUN useradd --system --uid 1069 --gid apprunner apprunner
COPY . .
EXPOSE 8080
CMD [ "python", "./app.py" ]