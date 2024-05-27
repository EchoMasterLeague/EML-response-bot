from python:3.11-slim

workdir /app

run pwd
run ls -la /

copy . ./
run pip install -r requirements.txt

copy . .

cmd ["python3", "Xena/main.py"]