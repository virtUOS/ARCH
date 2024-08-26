This guide describes how to deploy the ARCH application using Docker. 

# Contents
- [Prerequisites](#prerequisites)
- [configure settings and environment variables](#configure-settings-and-environment-variables)
- [Docker installation](#docker-installation)
- [Useful commands (for development)](#useful-commands-for-development)

# Prerequisites

### 1. Install git
```
sudo apt-get install git
``` 
or 
```
sudo apt install -y build-essential python-dev git
```

### 2. Clone the repository
```
sudo git clone [url of repository e.g. https://github.com/virtuos/ARCH]
```

### 3. Install Docker

**Note**: _see https://docs.docker.com/engine/install/debian/#installation-methods_
#### 3.1. Set up Docker's apt repository.
```
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```
#### 3.2. Install Docker Engine
```
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
#### 3.3 verify that the installation was successful
```
sudo docker run hello-world
```

### 4. Install Node.js and NPM
```
sudo apt-get install nodejs npm
```

### 5. Install Webpack
```
sudo npm install --save-dev webpack webpack-cli
```

### 6. Install frontend dependencies
```
sudo npm run build
```

# configure settings and environment variables

### 1. edit the .env files

**Note**: _Make sure to change the SECRET_KEY and the DB credentials._ 

Edit the `.env` files in the root directory of the project.
- Change the `SECRET_KEY` in the `env.dev` and `env.prod` files.
- Change the `SQL_USER` and `SQL_PASSWORD` in the `env.dev` and `env.prod` files.
- Change the `POSTGRES_USER` and `POSTGRES_PASSWORD` in the `env.db` file. 

**Note**: _The `env.db` file is used to configure the database in the `docker-compose.xxx.yml` files._

Activate optional functionalities by setting the corresponding environment variables in the `.env` files.
- set `ACTIVATE_FACE_DETECTION` to True to enable face detection.
- set `ACTIVATE_AI_SEARCH` to True to enable the AI-powered search and filter functionality.

If you do not want to use the optional functionalities, remove the respective lines from the Dockerfiles (i.e. `Dockerfile_prod`).

### 2. edit the nginx configuration

Change the nginx configuration in the `nginx/nginx.conf` file. 
Depending on your setup, you might need to add/edit the following:
- `server_name`,
- `client_max_body_size`,
- `ssl_certificate` and `ssl_certificate_key` paths.

#### 2. Generate a certificate for the application

Install Certbot and generate a certificate.

```
sudo apt install cerbot
sudo certbot certonly --standalone --preferred-challenges http -d example.com
```

**Note**: _To renew the certificate, run the following command._
```
sudo certbot renew --dry-run  # for testing
sudo certbot renew
```

# Docker deployment

**Note**: _Before building the image, give access to `entrypoint.prod.sh` or `entrypoint.dev.sh`._
```
chmod +x entrypoint.prod.sh
```

### 1. Build the image
```
sudo docker compose -f docker-compose.prod.yml build --no-cache
```

### 2. Start the container
```
sudo docker compose -f docker-compose.prod.yml up
```

**Note**: _If Postgres is already running on the host, you might need to stop it first._
``` 
# deactivate postgresql on the host to free the port
sudo lsof -i tcp:5432  # find the pid, usually on 5432
sudo kill <pid>        # kill the process
```

### 3. Create a superuser
```
sudo docker compose -f docker-compose.prod.yml exec web python arch/manage.py createsuperuser
```

### 4. Shut down the container
```
sudo docker compose -f docker-compose.prod.yml down
```
**Note**: _To remove the volumes, add the `-v` flag._

**Warning**: _This will delete all data stored in the database!_

# Useful commands (for development)

### migrate the database
```
sudo docker compose -f docker-compose.prod.yml exec web python arch/manage.py migrate
```

### populate the database with some data
```
docker compose -f docker-compose.prod.yml exec web python arch/manage.py populate_db
```

### run tests
```
sudo docker compose -f docker-compose.prod.yml exec web python arch/manage.py test arch_app.tests
```

### see logs
```
sudo docker compose logs
```

### inspect health of the containers
```
sudo docker ps
```
