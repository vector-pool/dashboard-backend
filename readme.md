# Install PostgreSQL with Docker

## Install Docker
If Docker is not already installed, you can install it using the following commands:

- For Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

- For CentOS/RHEL:
```bash
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
Verify Docker Installation:
```

- Check the docker is installed correctly:
```bash
docker --version
```

## Pull the PostgreSQL 14 Docker Image
Download the official PostgreSQL 14 Docker image from Docker Hub:

```bash
docker pull postgres:14
```
This will pull the latest PostgreSQL 14 image.

## Prepare the docker-compose.yml file
use sample docker-compose.yml file in root subnet directory.

## Running PostgreSQL with Docker

- Running docker
```bash
docker-compose up -d
```

- Verify the setup
```bash
docker ps
```

- Stop the docker
```bash
docker-compose down
```

- Connect to PostgreSQL
```bash
psql -h localhost -U <user_name> -d <db_name> -p <port>
```


