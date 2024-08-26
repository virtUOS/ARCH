This guide describes how to deploy the ARCH application on a server running on an Ubuntu OS, using PostgreSQL as a database, Gunicorn as a WSGI application server, and Nginx as a reverse proxy. This is one example setting which can be used in production. 

# Prerequisites

#### 1. Install Python

``` 
sudo apt install python3.10 
```

**Note**: _Currently running Python 3.10.6_

#### 2. Install pip

```
sudo apt install python3-pip
```

#### 3. Install git
```
sudo apt-get install git
``` 
or 
```
sudo apt install -y build-essential python-dev git
```

#### 4. Install venv
```
sudo apt-get install python3.10-venv
```

#### 5. Create a virtual environment

**Note**: _Create the virtual environment at the location where the project will be cloned, e.g. `cd` into `opt/`. Change `my_env` to an appropriate name._

```
python3 -m venv my_env
```

#### 6. Activate the environment

**Note**: _Assuming you are in the parent directory in which the virtual environment was created._

```
source my_env/bin/activate
``` 
or 
```
. my_env/bin/activate
```

#### 7. Clone the repository

```
sudo git clone [url of repository e.g. https://github.com/example/ARCH]
```

#### 8. Install requirements

**Note**: _Make sure the virtual environment is activated._
```
sudo pip install -r requirements.txt
```
**Note**: _For python-magic, install the libmagic C library, if not yet installed. (See [https://pypi.org/project/python-magic/](https://pypi.org/project/python-magic/) for the documentation)_
```
sudo apt-get install libmagic1
```

#### 9. Install FFmpeg

**Note**: _Install FFmpeg to enable formatting of video and audio._
```
sudo apt-get install ffmpeg
```

#### 10. Install Node.js and NPM

```
sudo apt-get install nodejs npm
```

#### 11. Install Webpack

```
sudo npm install --save-dev webpack webpack-cli
```

# Create build and bundle static assets

```
sudo npm run build
sudo python manage.py collectstatic
```

# Activate optional Features:
Enabling enhanced search and automatic Face Detection may require additional computational resources (e.g., additional RAM, Installing Deep Learning libraries).

#### 1. AI-powered search:
Follow the steps below to activate the Deep learning models that enrich the search module.
- In `settings.py` set `ACTIVATE_AI_SEARCH = True`
- Activate the virtual environment and install the required packages using these commands: `pip install torch==2.0.0` and `pip install sentence-transformers==2.2.2`

##### 1.1 Quantize CLIP models:
To quantize the `CLIP` models (used by the search module) and reduce the computational and memory costs during inference time (with little impact on the model's accuracy); in `settings.py` set `QUANTIZE_CLIP_MODELS = True`


#### 2. Face detection feature:
To activate the Face detection feature, follow the following instructions:
- In `settings.py` set `ACTIVATE_FACE_DETECTION = True`
- Activate the virtual environment and install `cvlib` using the command: `pip install cvlib==0.2.7` 


# Setup DB (PostgreSQL)

#### 1. Install PostgreSQL

```
sudo apt-get install postgresql postgresql-contrib
```

#### 2. Create a DB

open the db shell, e.g. via `postgres psql` or `sudo -u postgres psql`. Create a DB and an admin user to allow access to the DB from the Django application.

**Note**: _Change the name of the DB, the admin user and the password according to the configurations in the `settings.py` file of your Django application._

```
CREATE DATABASE arch_db;
CREATE USER db_admin WITH PASSWORD 'arch';
ALTER ROLE db_admin SET client_encoding TO 'utf8';
ALTER ROLE db_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE db_admin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE arch_db TO db_admin;
```

**Helpful commands for working with a PostgreSQL DB:**

- To exit SQL prompt `\q`

- To drop and recreate the DB: 
  ```
  DROP DATABASE arch_db;
  CREATE DATABASE arch_db;
  GRANT ALL PRIVILEGES ON DATABASE arch_db TO db_admin;
  ```

- In case you encounter a problem with the user permissions: 
  ```
  ALTER USER db_admin CREATEDB; 
  ```


#### 3. Create migrations and migrate

**Note**: _Assuming you are in the project directory in which `manage.py` is, and the virtual environment is activated._

```
sudo python manage.py makemigrations arch_app --settings=arch.settings
sudo python manage.py migrate --settings=arch.settings
```

# Configure Django application

#### 1. Set the Secret Key

```
echo "export SECRET_KEY='$(openssl rand -hex 40)'" > .DJANGO_SECRET_KEY
source .DJANGO_SECRET_KEY
```

Check if the secret key was generated.
```
cat .DJANGO_SECRET_KEY
```

#### 2. Set Debug to False 

```
export DJANGO_DEBUG=False
```


#### 3. Generate a certificate for the application

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

# Configure WSGI application (Gunicorn)

#### 1. Install Gunicorn
```
python -m pip install gunicorn
```

#### 2. Test Gunicorn

- Find the location where gunicorn was installed. `cd` into the directory that contains both the project and the environment directories (or the root dir if gunicorn is not found in either of those directories). 
  ```
  find . -name gunicorn
  ```
- Generate absolute path.
  ``` 
  readlink -f env/bin/gunicorn
  ```

- In the Django project, `cd`  into the directory `ARCH/arch` and run the command below to test that gunicorn is working.
  ```
  /opt/env/bin/gunicorn arch.wsgi:application --workers=2 --threads=1 --bind 0.0.0.0:8000
  ```

  **Note**: _Use `ctrl + z` to detach the running process that currently blocks the shell. Then run `bg` command to set it as a background process. (run `fg` to go back to the process running)_

- Ping the server to test that gunicorn is running correctly.

  **Note**: _In case curl is not installed, run `apt install curl`_

  ```
  curl -I http://127.0.0.1:8000
  ```
 

#### 3. Create Gunicorn service file

Create and open a `systemd` service file for gunicorn. 

**Note**: _Adapt the name of the service accordingly._ 

```
vim /etc/systemd/system/arch.service
```

Example:

```
[Unit]
Description=my_app Service Test
Documentation=https://example.com
Wants=network.target

[Service]
Type=simple
ExecStart=/opt/env/bin/gunicorn my_app.wsgi:application --workers=2 --threads=1 --bind 127.0.0.1:8000
WorkingDirectory=/opt/my_app
Restart=always
```


If you make changes to the `/etc/systemd/system/arch.service` file; run:

```
sudo systemctl daemon-reload
sudo systemctl restart arch 
```

Check the status of the service (it should be active):

```
sudo systemctl status arch
```

Display the logs of the service:

```
sudo journalctl --unit=arch
```


# Configure reverse proxy server (NGINX)

#### 1. Install Nginx

**Note**: _NGINX usually starts automatically after installation._

```
apt install nginx
````

#### 2. Create Nginx service file 

**Note**: One can either adapt the existing `nginx.conf` or create a new config file. This example is for adapting the `nginx.conf` file.

```
vim /etc/nginx/nginx.conf

```
Example:

```
# nginx_example.conf

events {
    worker_connections 768;

    }

# Configuration specific to HTTP and affecting all virtual servers
http {

      log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                                        '$status $body_bytes_sent "$http_referer" '
                                       '"$http_user_agent" "$http_x_forwarded_for"';

      access_log  /var/log/nginx/access.log  main;
      client_max_body_size 1024M;
      sendfile            on;
      tcp_nopush          on;
      keepalive_timeout   65;
      types_hash_max_size 4096;
      include             /etc/nginx/mime.types;
      default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    # See http://nginx.org/en/docs/ngx_core_module.html#include
    # for more information.
    include /etc/nginx/conf.d/*.conf;



     # configuration of HTTP virtual server
     server {
              listen 80;
              listen [::]:80;
              server_name example.de;

              location / {
                  return 301 https://example.de$request_uri;
                }
        }


     # HTTPS set-up
     server {
                listen      443 ssl http2;
                listen [::]:443 ssl http2;
                server_name example.de;

                ssl_certificate_key /etc/letsencrypt/live/example.de/privkey.pem;
                ssl_certificate     /etc/letsencrypt/live/example.de/fullchain.pem;

                client_max_body_size 1024M;

                location / {
                    client_max_body_size 1024M;
                    proxy_set_header    Host $host;
                    proxy_set_header    X-Real-IP $remote_addr;
                    proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
                    proxy_set_header    X-Forwarded-Proto $scheme;
                    proxy_pass          http://127.0.0.1:8000;
              }

                location /static {
                      alias /opt/my_app/static/;
                }

                location /media/ {
                alias /opt/my_app/media/;
              }
        }


 }

```

# Configure Task Queue service

Create and open a `systemd` service file for the task queue. 

**Note**: _Adapt the name of the service accordingly._ 

```
vim /etc/systemd/system/arch_task_q.service
```

Example:

```
[Unit]
Description=ARCH Task Queue
Documentation=https://example.com
Wants=network.target

[Service]
Type=simple
ExecStart=python manage.py qcluster --settings=arch.settings
WorkingDirectory=/opt/ARCH/arch/
Restart=always
```

