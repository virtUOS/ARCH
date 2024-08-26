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

echo "Checking if database is already migrated"
output=$(python arch/manage.py showmigrations)
if echo "$output" | grep -q "\[ \]";
then
    echo "Applying database migrations"
    python arch/manage.py migrate
    echo "Collecting static files"
    python arch/manage.py collectstatic --noinput
#    echo "populating database with initial data"
#    python arch/manage.py populate_db
else
    echo "Database is already migrated"
fi

exec "$@"
