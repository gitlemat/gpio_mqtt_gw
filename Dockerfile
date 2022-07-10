FROM python:3.7-alpine
LABEL maintainer="Sergio Ibanez <sibanezc@gmail.com>"

VOLUME /config
VOLUME /logs

COPY orangepi_PC_gpio_pyH3-master /tmp/orangepi_PC_gpio_pyH3-master
COPY requirements_all.txt /tmp/requirements_all.txt

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev && \ 
    pip3 install --no-cache-dir -r /tmp/requirements_all.txt && \
    cd /tmp/orangepi_PC_gpio_pyH3-master && \ 
    python3 setup.py install && \
    apk del .build-deps && \
    rm -rf /var/cache/apk/* /tmp/* 

CMD [ "python3", "/config/mqtt_srv.py" ]
