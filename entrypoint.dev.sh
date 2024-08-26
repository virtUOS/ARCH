#!/bin/sh

# Exit on error
set -e

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."
    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 1
    done
    echo "PostgreSQL started"
fi

echo "Applying database migrations"
python arch/manage.py flush --no-input
python arch/manage.py migrate

# Delete media files
#echo "Deleting media files"
#rm -rf arch/media/*

echo "Collecting static files"
python arch/manage.py collectstatic --noinput

echo "Populating database with initial data"
python arch/manage.py populate_db

exec "$@"
