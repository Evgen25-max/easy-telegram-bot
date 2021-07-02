FROM python:3.8.5
WORKDIR /code
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
CMD python easy-bot.py