ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy the source code into the container.
COPY client/ .
COPY grpc_config/ ./grpc_config/
COPY requirements.txt . 

# Download dependencies as a separate step to take advantage of Docker's caching.
# 1. Leverage a cache mount to /root/.cache/pip to speed up subsequent builds (pip install doesn't need to be re-run each time
# since packages are cached).
# 2. install packages
RUN --mount=type=cache,target=/root/.cache/pip \
python -m pip install -r requirements.txt

# Expose the port that the application will run on.
EXPOSE 5001

# Run the application.
CMD ["uvicorn", "client:app", "--host", "0.0.0.0", "--port", "5001"]