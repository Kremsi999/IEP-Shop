FROM python:3

RUN mkdir -p /opt/src/shop
WORKDIR /opt/src/shop

COPY shop/migrate.py ./migrate.py
COPY shop/configuration.py ./configuration.py
COPY shop/models.py ./models.py
COPY shop/decorators.py ./decorators.py
COPY shop/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/shop"

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT ["python", "./migrate.py"]