"""
logs view
"""

import logging
import os

from flask import current_app, jsonify

from . import blueprint

log = logging.getLogger(__name__)


@blueprint.route('/logs/<string:repo>')
def get_logs(repo):
    log_dir, log_files = current_app.backup_data.logs.get_logs_list(repo)
    return jsonify(dict(dir=log_dir, files=list(enumerate(log_files))))


@blueprint.route('/logs')
def get_all_logs():
    repos = dict(current_app.config["BACKUP_REPOS"])
    output = {}

    for repo, repo_config in repos.items():
        log_dir, log_files = current_app.backup_data.logs.get_logs_list(repo)
        data = []
        for logf in log_files:
            status, _, _ = current_app.backup_data.logs.get_log_status(os.path.join(log_dir, logf))
            data.append({'filename': logf, 'status': status})
        output[repo] = data
    return output


@blueprint.route('/logs/<string:repo>/<string:filename>')
def get_log_content(repo, filename):
    status, log_lines = current_app.backup_data.logs.get_log_content(repo, filename)
    return { 'status': status, 'content':  log_lines } if status else {}
