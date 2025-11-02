**1.Install Python**

Go to Google → search:

Download Python

Or use link: https://python.org/downloads/

During install → check the box “Add to PATH” ✅


**2.Download your GitHub repo**

You already have your GitHub repo, so:

Go to your repo on GitHub → Click green “Code” → Download ZIP
Right-click ZIP → Extract

**3. Open the folder**

Open the folder:

Gatech-Waitlist-Bot


Right-click empty space → Open in Terminal / Powershell

(Windows: you can also open in CMD)


**4. Create folders for the watcher**

Inside your repo, make a folder named:

watcher


**5.Make your .env file**

In the main folder (Gatech-Waitlist-Bot), right-click → New → Text File → rename to:

.env


Open it → paste: (read the regular readme.md for this explanation on term, CRNS, and poll_Seconds)

TERM=202602
CRNS=12345,67890
POLL_SECONDS=10
DISCORD_WEBHOOK_URL=


Change the CRNs to your class CRNs (ex: 88421,88109).

**6. Install the required libraries**

In your terminal (inside the repo folder), run:

python -m venv venv


Then:

Windows:

venv\Scripts\activate


Mac/Linux:

source venv/bin/activate


Then install watcher packages:

pip install -r watcher/requirements.txt

**7. Run the bot**

Still in the repo folder, run:

python watcher/main.py


You should see:

Watching CRNs...
CRN 88421: no seats yet
CRN 88421: no seats yet
...


When a seat opens 🚨:

🟢 OPEN SEAT — CRN 88421: 1 remaining
