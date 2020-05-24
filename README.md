# BorgWeb

This is project fork of [BorgWeb](https://borgweb.readthedocs.io)
Check the original project [here](https://github.com/borgbackup/borgweb)

However most of the original code has been rewritten in order to upgrade borgweb into a tool that can be used as a frontend to monitor backups from serveral repositories.

For instance, with several machine in a network doing regular (or manual) borg backups.
If all the backups are sent to a single borg server, using this version of borgweb allows monitoring them.

Keep in mind this is still in development and many things remain to be done.

![Screenshot](https://github.com/vche/borgweb/blob/master/etc/borgweb-vche.png)

![Screenshot](https://github.com/vche/borgweb/blob/master/etc/borgweb-logs-vche.png)

The main backup page shows:
* A graph with a timeline of all available backups for every repositories
* Details on each backups (timestamp, size...)
* Color based status of each backup (success, failure, warning)
* Manual rescan of all backups

The log page shows:
* For each repo in the config, the list of log files available and their exit code
* Once a log file is selected, its content is displayed on the right card

Example scripts are provided in [etc](https://github.com/vche/borgweb/tree/master/etc) to:
* Create a backup stored locally or in a remote server (can be put in a cron job)
* Start and stop borgweb using systemctl


TODO:
* Add links to logs to each backup (currently only the most recent one has is linked)
* Async backup scan to improve loading
* Manually run a backup script when configured

**Note**: Scanning all backups may take some time and when many backups are available, may take up to a minute.

## Configuration

Update [config.py](https://github.com/vche/borgweb/blob/master/borgweb/config.py) as required:

Configure the server address and port:
```python
HOST = '0.0.0.0'  # use 0.0.0.0 to bind to all interfaces
PORT = 5000  # ports < 1024 need root
DEBUG = True  # if True, enable reloader and debugger
```

Configure the path of the borg binary:
```python
#: borg / borgweb configuration
BORG_PATH="/usr/bin/borg"
```

Configure the time (in secs) after wich the backups are rescanned and the cache location.
Accessing or refreshing the interface will only rescan the backups if the last scan is older than the TTL (Manual scan can still be triggered form the UI)
```python
STATUS_CACHE_TTL=43200
STATUS_CACHE_PATH="/tmp/borgweb.cache"
```

Configure the repositories to scan.
Each repository must be configured with the following:
* Repository path (where actual backups are stored)
* Log path (where the logs of each backup for this repo are stored)
* Password for this repo backup
* Optionally a script that can be run to manually trigger a new backup (not yet implemented)

```python
BACKUP_REPOS = {
    # Repo  name
    "mediadwarf": {
        # Repo absolute path
        "repo_path": "/media/dwarfdisk/Backup/mediadwarf",

        # Repo logs absolute path, or relative to the main LOG_DIR
        "log_path": "/var/log/borg/mediadwarf",

        # Repo password
        "repo_pwd": "backup",

        # Command/script to run to manually start a backup.
        # If left empty or not specified, the backup won't be
        # manually runnable
        "script": "script",

        # Filled with discovered backups in the repo
        "backups": []
    },
    "dwarfpi": {
        "repo_path": "/media/dwarfdisk/Backup/dwarfpi",
        "log_path": "/var/log/borg/dwarfpi",
        "repo_pwd": "backup",
        "backups": []
    }
}
```

Those fields are currently unused and will be removed or implemented in future versions:
```python
#: borg / borgweb configuration
LOG_DIR = '/var/log/borg'
REPOSITORY = '/var/www/repo' #
NAME = 'localhost'
BORG_LOGGING_CONF = "/var/log/borg/logging.conf"
TO_BACKUP = "/var/www/borgWebDan"
BACKUP_CMD = "BORG_LOGGING_CONF={BORG_LOGGING_CONF} borg create --list --stats --show-version --show-rc {REPOSITORY}::{NAME}-{LOCALTIME} {TO_BACKUP} >{LOG_DIR}/test/{NAME}-{LOCALTIME} 2>&1 </dev/null"
```
