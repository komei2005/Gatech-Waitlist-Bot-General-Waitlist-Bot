**#How to pick the correct TERM code**

#Banner term format is YYYYTT where TT is:

#01 = Summer, 02 = Spring, 08 = Fall (varies by institution; at GT, Spring commonly shows 02, Fall 08).

#Confirm the active registration term code from OSCAR’s dynamic schedule page (you don’t need to log in). Use that code in .env as TERM.


**#CRNs to monitor**

#Get CRNs from the class search (public). Add them to .env as CRNS=12345,67890.

#Run it 24/7

**#Linux/macOS (background)**

#nohup python watcher/main.py > run.log 2>&1 &

#Windows (background)

#Use Task Scheduler to run python watcher\main.py on login or on a schedule.

#Docker (optional)

# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY watcher/requirements.txt .
RUN pip install -r requirements.txt
COPY watcher/ ./
COPY .env ./
CMD ["python", "main.py"]



**#Build & run:**

#docker build -t gt-watcher .
#docker run --env-file .env --name gtwatch gt-watcher

**#Tips**

#Labels change slightly between terms (“Seats: Maximum/Actual/Remaining”). The parser above is resilient, but if GT tweaks wording, open any section page in your browser, copy the text block, and adjust the regex in banner.py.

#Only watch; don’t auto-register. CAS + Duo will make automation brittle and may violate GT/USG rules. The watcher gives you a fast ping so you can hop in and register manually.

#Rate limits: Polling every 5–15 seconds is typically fine; be polite. Increase the interval if you monitor many CRNs.
