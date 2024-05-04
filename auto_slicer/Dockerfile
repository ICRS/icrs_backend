# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

################################################################################
# Pick a base image to serve as the foundation for the other build stages in
# this file.
#
# For illustrative purposes, the following FROM command
# is using the alpine image (see https://hub.docker.com/_/alpine).
# By specifying the "latest" tag, it will also use whatever happens to be the
# most recent version of that image when you build your Dockerfile.
# If reproducability is important, consider using a versioned tag
# (e.g., alpine:3.17.2) or SHA (e.g., alpine@sha256:c41ab5c992deb4fe7e5da09f67a8804a46bd0592bfdf0b1847dde0e0889d2bff).
ARG PYTHON_VERSION=3.10.12
FROM ubuntu:22.04 as base

################################################################################
# Create a stage for building/compiling the application.
#
# The following commands will leverage the "base" stage above to generate
# a "hello world" script and make it executable, but for a real application, you
# would issue a RUN command for your application's build process to generate the
# executable. For language-specific examples, take a look at the Dockerfiles in
# the Awesome Compose repository: https://github.com/docker/awesome-compose
FROM base as build
WORKDIR /app

# COPY . .
# RUN chmod +x ./Bambu_Studio_linux_ubuntu_01.09.00.60.AppImage
RUN apt-get update && apt-get install  -y \
    autoconf \
    build-essential \
    eglexternalplatform-dev \
    extra-cmake-modules \
    file \
    libcairo2-dev \
    libcurl4-openssl-dev \
    libdbus-1-dev \
    libglew-dev \ 
    libglu1-mesa-dev \
    libgtk-3-dev \
    libosmesa6-dev \
    libsecret-1-dev \
    libsoup2.4-dev \
    libssl3 \
    libssl-dev \
    libudev-dev \
    libwayland-dev \
    libwebkit2gtk-4.0-dev \
    libxkbcommon-dev \
    locales \
    locales-all \
    m4 \
    pkgconf \
    sudo \
    wayland-protocols \
    wget 
RUN apt install -y python3 \
    python3-pip  \
    unzip 
    
RUN wget https://github.com/bambulab/BambuStudio/releases/download/v01.09.01.58/Bambu_Studio_linux_ubuntu-v01.09.01.58.AppImage
RUN chmod +x Bambu_Studio_linux_ubuntu-v01.09.01.58.AppImage
RUN ./Bambu_Studio_linux_ubuntu-v01.09.01.58.AppImage --appimage-extract 
#RUN mv squashfs-root/bin/* . && rm -rf squashfs-root 
RUN chmod +x squashfs-root/bin/bambu-studio

WORKDIR /app/squashfs-root/bin/

COPY requirements.txt .
# FROM python:${PYTHON_VERSION}-slim as final

ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python3 -m pip install -r requirements.txt

COPY scripts/ scripts/
# RUN ls -al; ls scripts -al; ls /app/squashfs-root/bin; ls /app/ ; ls /;
RUN cd scripts && ./download.sh
COPY . . 

#  && python3 merge.py
# RUN ls -al ; ls scripts -al
# RUN cd scripts && python3 merge.py


################################################################################
# Create a final stage for running your application.
#
# The following commands copy the output from the "build" stage above and tell
# the container runtime to execute it when the image is run. Ideally this stage
# contains the minimal runtime dependencies for the application as to produce
# the smallest image possible. This often means using a different and smaller
# image than the one used for building the application, but for illustrative
# purposes the "base" image is used here.
# FROM base AS final

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
#ARG UID=10001
#RUN adduser \
#    --disabled-password \
#    --gecos "" \
#    --home "/nonexistent" \
#    --shell "/sbin/nologin" \
#    --no-create-home \
#    --uid "${UID}" \
#    appuser
#USER appuser

EXPOSE 80

# What the container should run when it is started.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
