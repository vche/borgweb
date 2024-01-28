import logging
class Config(object):
    """This is the basic configuration class for BorgWeb."""

    # builtin web server configuration
    HOST = '0.0.0.0'  # use 0.0.0.0 to bind to all interfaces
    PORT = 5000  # ports < 1024 need root
    DEBUG = True  # if True, enable reloader and debugger

    # Path to logfile. If left empty, logs will be sent to the console. Optional log leve, default is info
    LOG_FILE = ''
    LOG_LEVEL = logging.DEBUG

    # Base directory for relative paths specified in repos 'log_path'
    LOG_DIR = '/var/log/borg'

    # Path to borg backup tool
    BORG_PATH = "/usr/bin/borg"

    # Repo status cache configuration. Update period in secs (default 12h)
    STATUS_CACHE_UPDATE_PERIOD = 43200
    STATUS_CACHE_PATH = "/tmp/borgweb.cache"

    # Enable alarming on discord channel for failed backups
    ENABLE_DISCORD_ALARMING = False
    DISCORD_WEBHOOK = "1420474818:https://discord.com/api/webhooks/1127505560233333090/dGZjhM32M4Vd-Iy1B9H"
    DISCORD_WEBHOOK_USER = "Borg backup monitor"
    DISCORD_MESSAGE = "**{} Backups failed**:\n\n{}"
    DISCORD_MESSAGE_DEVICE = "- {}: Failed with status {} on {} at {}\n"

    BACKUP_REPOS = {
        # Repo  name
        "server1": {
            # Repo absolute path
            "repo_path": "/repos_backups/server1",

            # Repo logs absolute path, or relative to the main LOG_DIR
            "log_path": "/repos_logs/server1",

            # Repo password
            "repo_pwd": "backup",

            # Command/script to run to manually start a backup.
            # If left empty or not specified, the backup won't be
            # manually runnable. Not yet used
            "script": "script",
        },
        "server2": {
            "repo_path": "/repos_backups/server2",
            "log_path": "/repos_logs/server2",
            "repo_pwd": "backup",
        },
    }
