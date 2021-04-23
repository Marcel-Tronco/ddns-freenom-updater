FROM python:3.9-alpine3.13

WORKDIR /usr/src/app

COPY requirements.txt ./

COPY ddns-freenom-script.py ./

RUN pip install --no-cache-dir -r requirements.txt && touch current_ip.txt

CMD python ddns-freenom-script.py