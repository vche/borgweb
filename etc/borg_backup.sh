#!/bin/sh


# Setting this, so you won't be asked for your repository passphrase:
export BORG_PASSPHRASE='backup'
# or this to ask an external program to supply the passphrase:
#export BORG_PASSCOMMAND='pass show backup'

# Log file name format to include timestamp
LOG_FILE_NAME="$(hostname)-$(date +'%Y-%m-%dT%H%M%S').log"
LOG_FILE="/var/log/borg/$LOG_FILE_NAME"

# Local backup storage
export BORG_REPO=/media/backupdisk/backup/server1
REMOTE_LOG_FILE=""

# Remote backup storage: Enable and configure the following lines
#BORG_SERVER=user@server1.local
#export BORG_REPO=ssh://$BORG_SERVER/media/backupdisk/backup/server2
#REMOTE_LOG_FILE="$BORG_SERVER:/var/log/borg/server2/$LOG_FILE_NAME"

# some helpers and error handling:
info() { printf "\n%s %s\n\n" "$( date )" "$*" >&2; }
trap 'echo $( date ) Backup interrupted >&2; exit 2' INT TERM

backup()
{
  info "Starting backup"

  # Backup the most important directories into an archive named after
  # the machine this script is currently running on:

  borg create                         \
      --verbose                       \
      --filter AME                    \
      --list                          \
      --stats                         \
      --show-rc                       \
      --compression lz4               \
      --exclude-caches                \
      --exclude '/home/*/.cache/*'    \
      --exclude '/etc/apt'            \
                                    \
      ::'{hostname}-{now}'            \
      /etc                            \
      /home/user/.config               \
      /home/user/.kodi                 \
      /home/user/.vim*                 \
      /home/user/.bash*                \
      /home/user/.gnupg                \
      /home/user/.profile              \
      /home/user/.ssh                  \
      /home/user/.zshrc                \
      /home/user/.oh-my-zsh            \
      /home/user/bin                   \
      /home/docker                    \

}

prune()
{
  info "Pruning repository"

  # Use the `prune` subcommand to maintain 7 daily, 4 weekly and 6 monthly
  # archives of THIS machine. The '{hostname}-' prefix is very important to
  # limit prune's operation to this machine's archives and not apply to
  # other machines' archives also:

  borg prune                          \
      --list                          \
      --prefix '{hostname}-'          \
      --show-rc                       \
      --keep-daily    7               \
      --keep-weekly   4               \
      --keep-monthly  6               \

}

print_status()
{
  if [ $1 -eq 0 ]; then
      info "Backup and Prune finished successfully"
  elif [ $1 -eq 1 ]; then
      info "Backup and/or Prune finished with warnings"
  else
      info "Backup and/or Prune finished with errors"
  fi
}


touch $LOG_FILE

backup 2>>$LOG_FILE
backup_exit=$?

prune 2>>$LOG_FILE
prune_exit=$?

# use highest exit code as global exit code
global_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))
print_status $global_exit 2>>$LOG_FILE

# Append the backup status again for borgweb compatibility
echo "$(date +'%Y-%m-%d %H:%M:%S') [INFO] terminating with success status, rc ${global_exit}" >>$LOG_FILE

# Copy to remote server if configured
if [ "$REMOTE_LOG_FILE" != "" ]; then
  echo "scp $LOG_FILE $REMOTE_LOG_FILE"
  scp $LOG_FILE $REMOTE_LOG_FILE
fi

exit ${global_exit}

