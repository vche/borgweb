#!/bin/bash

# Location of the log files. Recusrively checked for logs
BORG_LOGS=/media/dwarfdisk/Backup/logs

# Location of the backups. The log will be deleted if the backup is not found
BORG_REPOS=/media/dwarfdisk/Backup/

# Minimal log age to be considered for deletion
LOG_MIN_AGE=7

BORG_PWD='backup'

declare -A REPOS_BACKUPS

read_repo() {
    if [[ "${REPOS_BACKUPS[$1]}" == "" ]] && [ -d $BORG_REPOS/$1 ]; then
        echo "Reading repo $1"
        REPOS_BACKUPS[$1]="$(sudo BORG_PASSPHRASE=$BORG_PWD borg list $BORG_REPOS/$1)"
	return 1
    else
	return 2
    fi
}

is_in_repo() {
    #echo "checking log $1"
    if [[ "${REPOS_BACKUPS[$2]}" == *"$1"* ]]; then
        #echo "d$1 FOUND"
        return 1
    else
        return 2
    fi
}

# Check if the backup in the logs exist, or delete the log
check_log() {
    # Extract repo and backup names using regex
    if [[ $(cat $1 | grep "Creating archive") =~ \".*\/(.*)\:\:(.*)\" ]]; then 
        REPO=${BASH_REMATCH[1]}
        BACKUP=${BASH_REMATCH[2]}
        read_repo $REPO
        is_in_repo $BACKUP $REPO
        return $?
    else
        echo "WARNING: Ignoring $1"
    fi
}

while getopts ":hl:r:a:p:" opt; do
    case ${opt} in
        h )
            echo "Usage: cmd [-h] [-l <log path>] [-r <repo path>] [-a <minimal log age in days>] [-p <borg backup password>]"
            exit
        ;;
        l )
            BORG_LOGS=$OPTARG
        ;;
        r )
            BORG_REPOS=$OPTARG
        ;;
        a )
            LOG_MIN_AGE=$OPTARG
        ;;
        p )
            BORG_PWD=$OPTARG
        ;;
        \? )
            echo "Invalid option: $OPTARG" 1>&2
            exit
        ;;
        : )
            echo "Invalid option: $OPTARG requires an argument" 1>&2
            exit
        ;;
    esac
done
shift $((OPTIND -1))

# Get all older logs and check if they should be kept
LOG_LIST=$(find $BORG_LOGS -mtime +$LOG_MIN_AGE -name "*.log")
for LOG in $LOG_LIST; do
    check_log $LOG
    if [[ "$?" == "2"  ]]; then
        echo "Removing log $LOG"
	rm $LOG
    fi
done
