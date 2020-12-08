#!/bin/env bash

echo "启动web..."
python manage.py makemigrations 
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
echo "done."