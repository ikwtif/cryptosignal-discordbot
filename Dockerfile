FROM python:3.8.7-alpine3.11



ADD app/ /app
WORKDIR /app



RUN pip install -r requirements.txt


CMD ["/usr/local/bin/python", "-u", "app.py"]