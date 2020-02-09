FROM python:latest

WORKDIR /app

COPY . .

RUN groupadd -g 12345 twitchlive

RUN adduser --system --uid 12345 --gid 12345 twitchlive

RUN chown -R twitchlive:twitchlive /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "main.py"]