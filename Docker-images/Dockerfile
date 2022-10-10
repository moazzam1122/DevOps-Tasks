FROM ubuntu:18.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install software-properties-common -y && apt-get update -y && apt-get install awscli -y

COPY entry.sh /usr/bin/entry.sh
RUN chmod +x /usr/bin/entry.sh

ENTRYPOINT ["/usr/bin/entry.sh"]