"""
backup view
"""

import subprocess
import time

from flask import current_app, render_template, jsonify
from . import blueprint
from . import logs
from borgweb.borg import BorgClient

process = None


@blueprint.route('/backups', methods=['GET'])
def get_backups():
    repos = dict(current_app.config["BACKUP_REPOS"])
    output = {}
    borg = BorgClient(current_app.config["BORG_PATH"])

    for repo, repo_config in repos.items():
        repo_data = {}
        repo_data["backups"] = []

        # Get repo info
        borg.set_repo(repo_config["repo_path"], pwd=repo_config["repo_pwd"])
        borg_info = borg.info()
        repo_data.update(borg_info)

        # Get backup list
        borg_list = borg.list()
        repo_data["backups"].extend(borg_list)

        # Set the default status to not run
        repo_data["last_result"] = "warning"
        repo_data["last_date"] = ""
        repo_data["last_time"] = ""

        # Get last info run for this repo
        #TODO Configure number of run status to get
        log_dir, log_files = logs._get_logs(repo)
        if(len(log_files) > 0):
            repo_data["last_result"], repo_data["last_date"], repo_data["last_time"] = logs.getLogFileStatus(log_dir + "/" + log_files[0])

        # Get details on each bqckup
        for backup in repo_data["backups"]:
            #TODO: Get borg info on repo
            borg_archinfo = borg.info(archive=backup["name"])
            backup.update(borg_archinfo)
            print(f"oka.... {borg_archinfo}")
            #backup["date"] = "1-2-3 1:2:3"
            #backup["size"] = "102gb"
            #backup["csize"] = "9gb"
            #backup["dsize"] = "1mb"

        output[repo] = repo_data
    return jsonify(output)
