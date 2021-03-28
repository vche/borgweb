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

    # Repo status cache configuration. TTL in secs
    STATUS_CACHE_TTL = 43200
    STATUS_CACHE_PATH = "/tmp/borgweb.cache"

    BACKUP_REPOS = {
        # Repo  name
        "server1": {
            # Repo absolute path
            "repo_path": "/path/to/backup/server1",

            # Repo logs absolute path, or relative to the main LOG_DIR
            "log_path": "/media/dwarfdisk/Backup/logs/mediadwarf",

            # Repo password
            "repo_pwd": "backup",

            # Command/script to run to manually start a backup.
            # If left empty or not specified, the backup won't be
            # manually runnable. Not yet used
            "script": "script",
        },
        "server2": {
            "repo_path": "/path/to/backup/server1",
            "log_path": "/media/dwarfdisk/Backup/logs/dwarfpi",
            "repo_pwd": "backup",
        },
    }
