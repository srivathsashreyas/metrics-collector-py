# configuration when spark master + worker + driver run in the same pod
# this is not a standard setup, but can be useful for testing or small workloads
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# install java and set java home (required for spark)
RUN apt-get update && apt-get install -y openjdk-21-jre-headless && apt-get clean
# use arm64 if building the image on a mac with apple silicon
#ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-arm64
# for intel/amd use the following line instead
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

WORKDIR /app

# Copy the source code into the container.
COPY processor/__init__.py .
COPY processor/processor.py .
COPY db ./db
COPY requirements.txt .
COPY processor/dependencies/jars ./jars

# Download dependencies as a separate step to take advantage of Docker's caching.
# 1. Leverage a cache mount to /root/.cache/pip to speed up subsequent builds (pip install doesn't need to be re-run each time
# since packages are cached).
# 2. install packages
RUN --mount=type=cache,target=/root/.cache/pip \
python -m pip install -r requirements.txt


# Run the application.
CMD ["python3","-m","processor"]