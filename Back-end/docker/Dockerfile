FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies, whose those ones are build-essential and libpq-dev. The build-essential package includes a collection of tools
#and libraries that are necessary for compiling and building software from source code, while the libpq-dev package provides the development
# files for PostgreSQL, which is a popular relational database management system. These dependencies are required to build and install the 
#application and its dependencies properly. After installing the dependencies, the command also cleans up the apt cache to reduce the size of
# the resulting Docker image.

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry and use it to install dependencies.
# With package-mode=false in pyproject.toml, pip install . would fail with
# "Building a package is not possible in non-package mode".
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

FROM python:3.12-slim AS production

WORKDIR /app

# Create a non-root user to have the application run under, which is a good security practice to avoid running the application as the root user inside the container.
#A group also is created because the user needs to be part of a group, and the group is named "psi" to 
#match the user name. The `-r` flag is used to create a system user and group, which are typically used 
#for running applications and services.
RUN groupadd -r psi && useradd -r -g psi psi

#In this case, further than libpq-dev, the curl package is also installed. The curl package is a command-line tool for transferring data with
# URLs, and it is often used for making HTTP requests. It may be required by the application or its dependencies to perform certain operations,
# such as fetching data from external APIs or services. Similar to the previous stage, the apt cache is cleaned up after installing the 
#dependencies to reduce the size of the resulting Docker image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the installed dependencies from the builder stage to the production stage. This includes the 
#Python packages that were installed in the builder stage, which are necessary for the application to
#run.
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code to the production stage. This includes all the source code and other files
#that are necessary for the application to run. The `COPY . .` command copies all files from the current
#directory (where the Dockerfile is located) to the `/app` directory in the container. This should include
#the main application code, configuration files, and any other necessary files for the application to 
#function properly.
COPY . .

# Change ownership of the application files to the non-root user created earlier, which ensures that
#the application runs with the appropriate permissions and does not have unnecessary access to system
#resources. The `-R` flag is used to change ownership recursively for all files and directories within
#the `/app` directory, and the `psi:psi` specifies that the user and group ownership should be set to 
#"psi".
RUN chown -R psi:psi /app
USER psi

EXPOSE 8000

# Command to run the application using Uvicorn, which is an ASGI (Asynchronous Server Gateway Interface) 
#server for Python web applications. The command specifies the application entry point 
#(`app.main:create_app`), indicates that it should be run as a factory function (`--factory`), and sets
#the host and port for the server to listen on. Additionally, it specifies that the server should use 4 worker processes 
#to handle incoming requests, which can help improve performance and scalability.
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
