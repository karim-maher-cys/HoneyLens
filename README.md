# HoneyLens
a cybersecurity news and threat-intel dashboard.
I built HoneyLens: a cybersecurity news and threat-intel dashboard. 🍯

What's REAL in this version:

✅ A Python collector that pulls security news every day from The Hacker News, BleepingComputer and Krebs on Security, removes duplicates, and tags each story (Ransomware, Vulnerability, Data breach, Malware)

✅ Famous vulnerabilities (Log4Shell, EternalBlue, Heartbleed, Shellshock, regreSSHion) explained in both English and Arabic

✅ Automated daily runs with Windows Task Scheduler, SQLite storage, and zero external dependencies

What's DEMO data:

⚠️ The attack sections (heatmap, top countries, credentials, commands) are simulated for now. They're clearly labeled "Demo data" in the dashboard.

Why? Real attack data needs a live honeypot exposed to the internet, and I want to deploy it safely and properly rather than rush it. Next step: connecting a Cowrie SSH honeypot so those sections run on real attacks.

Built with Python, SQLite, and Streamlit.

Code: [GitHub link]

Feedback welcome, especially from SOC and blue team folks.

#Cybersecurity #Python #ThreatIntelligence #BlueTeam #Honeypot #Streamlit #OSCP
