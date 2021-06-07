FROM python:3.9-alpine3.13

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY domain_records.json ./data/freenom_data.json
COPY ddns-freenom-script.py ./

CMD python ddns-freenom-script.py