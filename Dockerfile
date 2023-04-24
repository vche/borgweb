# FROM python:3
FROM ubuntu:jammy

RUN apt-get update && apt-get install -y --no-install-recommends \
        borgbackup \
        python3-pip \
        && \
        rm -rf /var/cache/apt /var/lib/apt/lists
ADD borgweb /borgweb
ADD setup.py /
ADD setup.cfg /
ADD etc/config.cfg /config/
ENV BORGWEB_CONFIG /config/config.cfg

RUN pip3 install virtualenv
RUN virtualenv /pyvenv

# Install dependencies:
WORKDIR /
RUN /pyvenv/bin/pip install -e .

# Run the application:
CMD ["/pyvenv/bin/borgweb"]

VOLUME /config
VOLUME /repos_backups
VOLUME /repos_logs
EXPOSE 5000
