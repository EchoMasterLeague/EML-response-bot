from python:3.11-slim

workdir /app

run pwd
run ls -la /

copy requirements.txt ./requirements.txt
run pip install -r requirements.txt

copy . .

workdir /app/Xena
cmd ["python3", "main.py"]