"""
logs view
"""

import logging
import os

from flask import current_app, jsonify

from . import blueprint

log = logging.getLogger(__name__)
SUCCESS, INFO, WARNING, DANGER = 'success', 'info', 'warning', 'danger'


def overall_classifier(f):
    end = f.seek(0, os.SEEK_END)
    f.seek(max(0, end - 250), os.SEEK_SET)  # len(last log line) < 250
    f.seek(0, os.SEEK_SET)
    lines = f.readlines()
    return overall_lines_classifier(lines)

def overall_lines_classifier(lines):
    try:
        line = lines[-1].rstrip('\n')
    except IndexError:
        return DANGER  # something strange happened, empty log?
    try:
        tokens = line.split(" ", 3)  # get from "date time level msg"
        line_date = tokens[0]
        line_time = tokens[1]
        line_msg = tokens[3]
    except IndexError:
        # unexpected log line format
        return DANGER, None, None

    # Default,  rc == 2 or other, or no '--show-rc given'
    status = DANGER
    if line_msg.startswith('terminating with'):
        if line_msg.endswith('rc 0'):
            status = SUCCESS
        elif line_msg.endswith('rc 1'):
            status = WARNING
    return status, line_date, line_time


def line_classifier(line):
    try:
        level = line.split(" ", 3)[2]  # get level from "date time level msg"
    except IndexError:
        # unexpected log line format
        level = 'ERROR'
    if level == 'INFO':
        return INFO
    if level == 'WARNING':
        return WARNING
    return DANGER

def _get_logdir(repo):
    log_dir = current_app.config['LOG_DIR']
    repo_logs = current_app.config['BACKUP_REPOS'][repo]['log_path']
    if repo_logs.startswith(os.sep):
        log_dir = repo_logs
    else:
        log_dir = os.path.join(log_dir, repo_logs)
    log_dir = os.path.abspath(log_dir)
    return log_dir

def _get_logs(repo):
    try:
        log_dir = _get_logdir(repo)
        log_files = os.listdir(log_dir)
    except (KeyError, OSError) as e:
        log_dir = ""
        log_files = []
        log.error(f"Invalid configuration: {e}")
    return log_dir, sorted(log_files, reverse=True)


def getLogFileStatus(log_file):
    with open(log_file, 'r') as f:
        f.seek(0, os.SEEK_END)
        return overall_classifier(f)


@blueprint.route('/logs/<string:repo>')
def get_logs(repo):
    log_dir, log_files = _get_logs(repo)
    return jsonify(dict(dir=log_dir,
                        files=list(enumerate(log_files))))

@blueprint.route('/logs')
def get_all_logs():
    repos = dict(current_app.config["BACKUP_REPOS"])
    output = {}

    for repo, repo_config in repos.items():
        log_dir, log_files = _get_logs(repo)
        data = []
        for logf in log_files:
            status, _, _ = getLogFileStatus(os.path.join(log_dir, logf))
            data.append({'filename': logf, 'status': status})
        output[repo] = data
    return output

@blueprint.route('/logs/<string:repo>/<string:filename>')
def get_log_content(repo, filename):
    log_data = {}
    try:
        log_dir = _get_logdir(repo)
        log_file = os.path.join(log_dir, filename)
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
        log_data['content'] = log_lines
        log_data['status'], _, _ = overall_lines_classifier(log_lines)
    except (KeyError, OSError) as e:
        log.error(f"Invalid configuration: {e}")

    return log_data
