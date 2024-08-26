# Prerequisites
1. Install Git: ```apt update && apt install -y git```
2. Install Python: ```apt update && apt install -y python3 python3-venv```


# Install
1. Download updateEvents.sh
2. Make script executable: ```chmod +x updateEvents.sh```
3. Open crontab from User Root: ```crontab -e```
4. Add the following line: ```0 6 * * * /path/to/updateEvents.sh```
