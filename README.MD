This is a dockerized python script updating the IP for a domain on freenom.com.

## Versions

There are two versions available. A default version and one that sends some login information to a designated telegram chat.




## Telegram-Logs 
It can also be used to forward some loging to a telegram chat of choice with a telegram bot of choice. (Both needs to be configured beforehand) 


## docker-compose example

    version: '3'
    
    services: 
        ddns_updater:  
          image: ddns-freenom:0.1.7
          container_name: ddns-trial
          build: .
          environment:
            - "FREENOM_EMAIL= < login >"
            - "FREENOM_PW= < password >"
            - "FREENOM_DOMAIN_NAME= < domain name >"
            - "FREENOM_DOMAIN_ID= < domain id >"
            - "TELEGRAM_BOT_ID= < telegram bot id >"
            - "TELEGRAM_CHAT_ID= < tlegram chat id > "
            - 'DNS_JSON={
                "dnsaction": "modify",
                "records[0][line]": "",
                "records[0][type]": < type of first record >, # e.g. A
                "records[0][name]": < name >,
                "records[0][ttl]": < update time >,
                "records[1][line]": "",
                "records[1][value]": < target >
                < ... and so on for every other record you wanna set for the domain in question >
              }'