class Config(object):
    """This is the basic configuration class for BorgWeb."""

    #: builtin web server configuration
    HOST = '0.0.0.0'  # use 0.0.0.0 to bind to all interfaces
    PORT = 5000  # ports < 1024 need root
    DEBUG = True  # if True, enable reloader and debugger

    #: borg / borgweb configuration
    LOG_DIR = '/var/log/borg'
    BORG_PATH="/usr/bin/borg"

    # Repo status cache configuration. TTL in secs
    STATUS_CACHE_TTL=43200
    STATUS_CACHE_PATH="/tmp/borgweb.cache"

    # Unused
    REPOSITORY = '/var/www/repo' #
    NAME = 'localhost'
    BORG_LOGGING_CONF = "/var/log/borg/logging.conf"
    TO_BACKUP = "/var/www/borgWebDan" # unused ?

    # when you click on "start backup", this command will be given to a OS
    # shell to execute it.
    # if you just need something simple (like "borg create ..."), just put
    # the command here. if you need something more complex, write a script and
    # call it from here.
    # commands will be executed as the same user as the one used for running
    # borgweb. for running commands as root, you'll need to use sudo (and
    # configure it in an appropriate and secure way).
    # template placeholders like {LOG_DIR} (and other stuff set in the config)
    # will be expanded to their value before the shell command is executed.
    BACKUP_CMD = "BORG_LOGGING_CONF={BORG_LOGGING_CONF} borg create --list --stats --show-version --show-rc {REPOSITORY}::{NAME}-{LOCALTIME} {TO_BACKUP} >{LOG_DIR}/test/{NAME}-{LOCALTIME} 2>&1 </dev/null"

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
