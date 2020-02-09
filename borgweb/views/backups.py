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
    output = { "repos": {}, "bargraph":[] }
    borg = BorgClient(current_app.config["BORG_PATH"])

    for repo, repo_config in repos.items():
        repo_data = {}
        repo_graph = {"type": "bar", "name": repo, "x":[], "y":[]}
        repo_data["backups"] = []
        repo_data["script"] = repo_config.get("script", "")


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
        repo_data["archives"] = len(repo_data["backups"])

        # Get last info run for this repo
        #TODO Configure number of run status to get
        log_dir, log_files = logs._get_logs(repo)
        if(len(log_files) > 0):
            repo_data["last_result"], repo_data["last_date"], repo_data["last_time"] = logs.getLogFileStatus(log_dir + "/" + log_files[0])

        # Get details on each backup
        for backup in repo_data["backups"]:
            borg_archinfo = borg.info(archive=backup["name"])
            backup.update(borg_archinfo)
            repo_graph["x"].append(borg_archinfo["date"])
            repo_graph["y"].append(borg_archinfo["size"])

        output["repos"][repo] = repo_data
        output["bargraph"].append(repo_graph)
    return jsonify(output)
