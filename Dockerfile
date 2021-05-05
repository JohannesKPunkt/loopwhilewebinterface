FROM ubuntu:20.04
LABEL maintainer="johannes.kern@fau.de"
LABEL version="0.1"

RUN apt-get update
RUN apt-get install -y python3-pip
RUN pip3 install TurboGears2 genshi transaction waitress autobahn[twisted,accelerate]
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y nginx
RUN apt-get install -y supervisor


# Create user
RUN useradd -M loopwhile
RUN usermod -L loopwhile

# Install loopwhile web interface
RUN mkdir -p /opt/loopwhile/logs
RUN mkdir -p /tmp/loopwhile
COPY . /tmp/loopwhile
WORKDIR /tmp/loopwhile
RUN /tmp/loopwhile/deliver.sh
RUN rm -r /tmp/loopwhile
WORKDIR /tmp

# Setup nginx
COPY config/nginx.example /etc/nginx/sites-available/default

# Setup supervisor
RUN mkdir -p /var/log/supervisor
COPY config/supervisord.conf /etc/supervisor/conf.d/loopwhile.conf


CMD ["/usr/bin/supervisord"]
