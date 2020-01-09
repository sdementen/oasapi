FROM python:3.6-slim-buster
WORKDIR /opt
COPY . .
RUN pip install -e .
RUN ls -a
ENTRYPOINT ["oasapi"]
CMD []

