FROM python:3.9.6-slim

LABEL maintainer="muneeb.gandapur@gmail.com"

WORKDIR comet
COPY . ./
RUN apt update -y && apt install git -y
RUN pip install -e .

WORKDIR project
ENTRYPOINT ["comet"]