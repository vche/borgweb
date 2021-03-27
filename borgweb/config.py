class Config(object):
    """This is the basic configuration class for BorgWeb."""

    # builtin web server configuration
    HOST = '0.0.0.0'  # use 0.0.0.0 to bind to all interfaces
    PORT = 5000  # ports < 1024 need root
    DEBUG = True  # if True, enable reloader and debugger

    # Path to logfile. If left empty, logs will be sent to the console
    LOG_FILE = ''

    # Base directory for relative paths specified in repos 'log_path'
    LOG_DIR = '/var/log/borg'

    # Path to borg backup tool
    BORG_PATH = "/usr/bin/borg"

    # Repo status cache configuration. TTL in secs
    STATUS_CACHE_TTL = 43200
    STATUS_CACHE_PATH = "/tmp/borgweb.cache"

    BACKUP_REPOS = {
        # Repo  name
        "mediadwarf": {
            # Repo absolute path
            "repo_path": "/media/dwarfdisk/Backup/mediadwarf",

            # Repo logs absolute path, or relative to the main LOG_DIR
            "log_path": "/media/dwarfdisk/Backup/logs/mediadwarf",

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
            "log_path": "/media/dwarfdisk/Backup/logs/dwarfpi",
            "repo_pwd": "backup",
            "backups": []
        },
        "domodwarf": {
            "repo_path": "/media/dwarfdisk/Backup/domodwarf",
            "log_path": "/media/dwarfdisk/Backup/logs/domodwarf",
            "repo_pwd": "backup",
            "backups": []
        }
    }

