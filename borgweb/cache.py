import logging
import time

import os
from borgweb.views import logs
import json
from pathlib import Path

log = logging.getLogger(__name__)


class BackupLogs:
    SUCCESS, INFO, WARNING, DANGER = 'success', 'info', 'warning', 'danger'

    def __init__(self, log_dir, repo_config):
        self._log_dir = log_dir
        self._repo_config = repo_config

    def _overall_classifier(self, f):
        # Determine the log status of a log file
        end = f.seek(0, os.SEEK_END)
        f.seek(max(0, end - 250), os.SEEK_SET)  # len(last log line) < 250
        f.seek(0, os.SEEK_SET)
        lines = f.readlines()
        return self.overall_lines_classifier(lines)

    def overall_lines_classifier(self, lines):
        # Determine the log status based on the status found in the specified log lines
        try:
            line = lines[-1].rstrip('\n')
        except IndexError:
            return self.DANGER  # something strange happened, empty log?
        try:
            tokens = line.split(" ", 3)  # get from "date time level msg"
            line_date = tokens[0]
            line_time = tokens[1]
            line_msg = tokens[3]
        except IndexError:
            # unexpected log line format
            return self.DANGER, None, None

        # Default,  rc == 2 or other, or no '--show-rc given'
        status = self.DANGER
        if line_msg.startswith('terminating with'):
            if line_msg.endswith('rc 0'):
                status = self.SUCCESS
            elif line_msg.endswith('rc 1'):
                status = self.WARNING
        return status, line_date, line_time

    def line_classifier(self, line):
        # Determine log status based on the line log level
        try:
            level = line.split(" ", 3)[2]  # get level from "date time level msg"
        except IndexError:
            # unexpected log line format
            level = 'ERROR'
        if level == 'INFO':
            return self.INFO
        if level == 'WARNING':
            return self.WARNING
        return self.DANGER

    def _get_repo_logdir(self, repo):
        repo_log_dir = self._log_dir
        repo_logs = self._repo_config[repo].get('log_path')
        if repo_logs:
            if repo_logs.startswith(os.sep):
                repo_log_dir = repo_logs
            else:
                repo_log_dir = os.path.join(self._log_dir, repo_logs)
                repo_log_dir = os.path.abspath(repo_log_dir)
        return repo_log_dir

    def get_logs_list(self, repo):
        try:
            repo_log_dir = self._get_repo_logdir(repo)
            log_files = os.listdir(repo_log_dir)
        except (KeyError, OSError) as e:
            repo_log_dir = ""
            log_files = []
            log.error(f"Invalid configuration: {e}")
        return repo_log_dir, sorted(log_files, reverse=True)

    def get_log_status(self, log_file):
        with open(log_file, 'r') as f:
            f.seek(0, os.SEEK_END)
            return self._overall_classifier(f)

    def get_last_log_status(self, repo):
        last_logfile, last_result, last_date, last_time = (None, None, None, None)
        log_dir, log_files = self.get_logs_list(repo)
        if(len(log_files) > 0):
            last_logfile = log_files[0]
            last_result, last_date, last_time = self.get_log_status(log_dir + "/" + last_logfile)
        return last_logfile, last_result, last_date, last_time

    def get_log_content(self, repo, filename):
        status = None
        log_lines = []
        try:
            log_dir = self._get_repo_logdir(repo)
            log_file = os.path.join(log_dir, filename)
            with open(log_file, 'r') as f:
                log_lines = f.readlines()
            status, _, _ = self.overall_lines_classifier(log_lines)
        except (KeyError, OSError) as e:
            log.error(f"Invalid configuration: {e}")

        return status, log_lines


class BackupsData:

    def __init__(self, data_path, repo_config, borg_client, log_dir):
        self._data_path = Path(data_path)
        self._repo_config = repo_config
        self._borg_client = borg_client
        self.backup_data = None
        self.logs = BackupLogs(log_dir, repo_config)
        self.load()

    def flush(self):
        # Invalidate the cache by removing the file
        if self._data_path and self._data_path.is_file():
            os.remove(self._data_path)
            log.info(f"Backups cache at {self._data_path} flushed")
        self.backup_data = None

    def load(self):
        if self._data_path and self._data_path.is_file():
            log.info(f"Loading backups cache from {self._data_path}")
            with open(self._data_path, "r") as f:
                self.backup_data = json.load(f)
        else:
            log.info(f"No backups cache found at {self._data_path}")
            # return self.create()
        return self.backup_data

    def save(self, data = None):
        with open(self._data_path, "w") as f:
            json.dump(data or self.backup_data, f)
            log.info(f"Backups cache saved to {self._data_path}")

    def create(self):
        repos = dict(self._repo_config)
        status_data = { "repos": {}, "bargraph":[] }

        log.info(f"Creating backups status")
        for repo, repo_config in repos.items():
            # Init the entry for this repo
            repo_data = {
                "backups": [],
                "script": repo_config.get("script", ""),
                "last_result": "warning",
                "last_date": "",
                "last_time": "",
                "ctime": time.ctime(),
            }

            # Get repo info from borg
            self._borg_client.set_repo(repo_config["repo_path"], pwd=repo_config["repo_pwd"])
            borg_info = self._borg_client.info()
            repo_data.update(borg_info)

            # Get backup list
            borg_list = self._borg_client.list()
            repo_data["backups"].extend(borg_list)
            repo_data["archives"] = len(repo_data["backups"])

            # Get last run info for this repo
            run_info = self._get_last_run(repo)
            repo_data.update(run_info)

            # Get details on each backup
            repo_graph = {"type": "bar", "name": repo, "x": [], "y": []}
            for backup in repo_data["backups"]:
                borg_archinfo = self._borg_client.info(archive=backup["name"])
                if borg_archinfo:
                    backup.update(borg_archinfo)
                    if "date" in borg_archinfo and borg_archinfo.get("size"):
                        repo_graph["x"].append(borg_archinfo["date"])
                        repo_graph["y"].append(borg_archinfo["size"])
                    else:
                        log.error(f"Backup {borg_archinfo} has no date/size")
                else:
                    log.info(f"No information for repo {backup['name']}")

            status_data["repos"][repo] = repo_data
            status_data["bargraph"].append(repo_graph)
            status_data["ctime"] = time.ctime()

        # Convert the data to json, cache it and return it
        self.save(status_data)
        log.info("Backups status created")
        return status_data

    def _get_last_run(self, repo):
            last_logfile, last_result, last_date, last_time = self.logs.get_last_log_status(repo)
            return {
                "last_log": last_logfile,
                "last_result": last_result,
                "last_date": last_date,
                "last_time": last_time,
            } if last_result else {}
