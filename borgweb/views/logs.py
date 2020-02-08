"""
logs view
"""

import os

from flask import current_app, render_template, jsonify, abort, request

from . import blueprint

SUCCESS, INFO, WARNING, DANGER = 'success', 'info', 'warning', 'danger'


def overall_classifier(f):
    end = f.seek(0, os.SEEK_END)
    f.seek(max(0, end - 250), os.SEEK_SET)  # len(last log line) < 250
    f.seek(0, os.SEEK_SET)
    lines = f.readlines()
    try:
        line = lines[-1].rstrip('\n')
    except IndexError:
        return DANGER  # something strange happened, empty log?
    try:
        tokens = line.split(" ", 3)  # get from "date time level msg"
        line_date = tokens[0]
        line_time = tokens[1]
        line_msg = tokens[3]
    except IndexError as e:
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


def _get_logs(repo):
    log_dir = current_app.config['LOG_DIR']
    try:
        repo_logs = current_app.config['BACKUP_REPOS'][repo]['log_path']
        log_dir = repo_logs
        if repo_logs.startswith(os.sep):
            log_dir = repo_logs
        else:
            log_dir = log_dir + "/" + repo_logs + "/"
        log_dir = os.path.abspath(log_dir)
        log_files = os.listdir(log_dir)
    except (KeyError, OSError) as e:
        log_files = []
        print(f"Invalid configuration: {e}")
    return log_dir, sorted(log_files, reverse=True)


def _get_log_lines(log_dir, log_file, offset, linecount=None, direction=1):
    log_file = os.path.join(log_dir, log_file)
    with open(log_file, 'r') as f:
        if direction == 1:  # forwards
            f.seek(offset)
            if linecount is None:  # read all, starting from offset
                log_lines = f.readlines()
            else:  # read n lines, starting from offset
                log_lines = []
                for i in range(linecount):
                    line = f.readline()
                    if not line:
                        break
                    log_lines.append(line)
            offset = f.tell()
        elif direction == -1:  # backwards
            log_lines = []
            if linecount is None:  # read all, up to offset
                start = 0
            else:  # read n lines, up to offset
                # we do not expect medium line length bigger than 1024
                start = max(0, offset - linecount * 1024)
            f.seek(start)
            current = 0
            while current < offset:
                line = f.readline()
                if not line:
                    break
                current = f.tell()
                log_lines.append((current, line))
            if linecount is None:
                offset = 0
                log_lines = [line for _, line in log_lines]
            else:
                try:
                    offset = log_lines[-linecount-1][0]
                except IndexError:
                    offset = 0
                log_lines = [line for _, line in log_lines[-linecount:]]
        else:
            raise ValueError("give direction == 1 (forwards) or -1 (backwards)")
        log_lines = [line.rstrip('\n') for line in log_lines]
    return log_file, offset, log_lines


@blueprint.route('/logs/<string:repo>/<int:index>/<offset>:<linecount>:<direction>')
def get_log_fragment(repo, index, offset, linecount, direction):
    try:
        offset = int(offset)
    except ValueError:
        offset = 0
    try:
        linecount = int(linecount)
    except ValueError:
        linecount = None
    try:
        direction = int(direction)
        if direction not in (-1, 1):
            raise ValueError
    except ValueError:
        direction = 1
    log_dir, log_files = _get_logs(repo)
    try:
        log_file = log_files[index]
    except IndexError:
        abort(404)
    log_file, offset, log_lines = _get_log_lines(log_dir, log_file, offset, linecount, direction)
    log_lines = [(line_classifier(line), line) for line in log_lines]
    return jsonify(dict(lines=log_lines, offset=offset))


@blueprint.route('/logs/<string:repo>/<int:index>')
def get_log(repo, index):
    log_dir, log_files = _get_logs(repo)
    try:
        log_file = log_files[index]
    except IndexError:
        abort(404)
    else:
        log_file = os.path.join(log_dir, log_file)
    with open(log_file, 'r') as f:
        length = f.seek(0, os.SEEK_END)
        status, _, _ = overall_classifier(f)
        return jsonify(dict(filename=log_file, status=status, length=length))

def getLogFileStatus(log_file):
    with open(log_file, 'r') as f:
        length = f.seek(0, os.SEEK_END)
        return overall_classifier(f)


@blueprint.route('/logs/<string:repo>')
def get_logs(repo):
    log_dir, log_files = _get_logs(repo)
    return jsonify(dict(dir=log_dir,
                        files=list(enumerate(log_files))))
