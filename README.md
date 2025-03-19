# Project 2 Testing Guide

This guide walks you through the commands to test my project on your local machine.

## 1. Install Python and required packages

Download Python 3 from Python's official site and add it to PATH. Then, go into your terminal and enter the command:

```bash

pip install pytest pytest-cov fastapi uvicorn cryptography sqlite3 jwt pyjwt

```
I also have a venv file and a requirements.txt if you would like to use them, but as I have never used venv before, I am unsure if I did it correctly.

## 2. Start the Application

Open your terminal and navigate to the project directory and use the commands:

```bash

cd "your_directory"

python project2.py

uvicorn project2:app --host 0.0.0.0 --port 8080 --reload

```

## 3. Gradebot Use

In another terminal navigate to the project directory with gradebot.exe in it and use the commands:

```bash

cd "your_directory"

.\gradebot.exe project2

```
## 4. Using the Test Cases

While running the server in another command prompt or the same one you used to run the gradebot use the command:

```bash

cd "your_directory"

pytest -cov

```

## In my testing I got a 65/65 on the gradebot

## The commands I used for the gradebot and for testing are in my testing.txt file if you want to see what I did.
