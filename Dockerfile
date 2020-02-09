FROM python:latest

WORKDIR /app

COPY . .

RUN groupadd -g 12345 twitchlive 

RUN adduser twitchlive -g 12345 -u 12345 -b /app

RUN chown -R twitchlive:twitchlive /app

CMD ["python", "main.py"]