FROM python:3

RUN mkdir -p /opt/src/shop
RUN mkdir -p /opt/src/shop/customer
WORKDIR /opt/src/shop

COPY shop/owner.py ./owner.py
COPY shop/configuration.py ./configuration.py
COPY shop/models.py ./models.py
COPY shop/decorators.py ./decorators.py
COPY shop/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/shop"

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT ["python", "./owner.py"]