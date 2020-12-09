#!/bin/env bash
source ~/.bashrc

echo "启动web..."
conda activate py3
python manage.py makemigrations 
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
echo "done."
