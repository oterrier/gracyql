FROM python:3.7-slim

# gracyql specific
ARG GRACYQL_PORT=8990
ARG TIMEZONE="Europe/Paris"

# Labels
LABEL version="1.0" \
      maintainer="Guillaume KARCHER <guillaume.karcher@kairntech.com>" \
      description="Dockerfile for Gracyql Container"

# Environment
USER root
ENV LANG="en_US.UTF-8"\
    LANGUAGE="en_US.UTF-8"

# Expose ports (8990[DE,EN,FR])
EXPOSE ${GRACYQL_PORT}

# Install prerequisites
RUN apt-get update -y && \
    apt-get install -y \
    wget \
    psmisc \
    net-tools \
    htop \
    telnet \
    curl \
    vim \
# gracyql specific
    gcc \
    python3-dev && \
# Final upgrade + clean
    apt-get update -y && \
    apt-get clean all -y

# Upgrade pip + install virtualenv
RUN pip install --upgrade pip && \
    pip3 install virtualenv

# Set timezone to Europe/Paris
RUN echo "${TIMEZONE}" > /etc/timezone && \
    ln -sf /usr/share/zoneinfo/${TIMEZONE} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

# Switch to gracyql
WORKDIR /app/kairntech/gracyql
# Add CMD: will start on port 8990
CMD . venv/bin/activate && python3 -m app.main

# Install spacy
RUN pip3 install spacy

# Copy gracyql sources
COPY . /app/kairntech/gracyql/

# Download spacy models (de, en, fr) +
# Install prereq asked by requirements.txt
RUN chmod +x /app/kairntech/gracyql/scripts/install && \
    bash scripts/install && \
    . venv/bin/activate && \
    python3 -m spacy download de && \
    python3 -m spacy download en && \
    python3 -m spacy download fr
