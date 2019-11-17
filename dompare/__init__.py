import argparse
import difflib
from http.server import HTTPServer, SimpleHTTPRequestHandler
import importlib
import logging
import logging.config
import os
import subprocess
import sys
import tempfile

import coloredlogs
from binaryornot.check import is_binary


def create_logger(is_verbose):
    # Suppress logging info from third-party packages
    logging.getLogger('binaryornot').setLevel(logging.ERROR)
    logging.getLogger('chardet').setLevel(logging.ERROR)

    FIELD_STYLES = dict(
        asctime=dict(color='red'),
        hostname=dict(color='magenta'),
        levelname=dict(color='yellow', bold=coloredlogs.CAN_USE_BOLD_FONT),
        filename=dict(color='magenta'),
        name=dict(color='blue'),
        threadName=dict(color='green')
    )

    LEVEL_STYLES = dict(
        debug=dict(color='white'),
        info=dict(color='cyan'),
        warning=dict(color='red'),
        error=dict(color='red'),
        critical=dict(color='red', bold=coloredlogs.CAN_USE_BOLD_FONT)
    )

    logger = logging.getLogger('dompare')
    level = 'DEBUG' if is_verbose else 'INFO'
    logging_level = logging.DEBUG if is_verbose else logging.INFO
    logger.setLevel(logging_level)

    coloredlogs.install(
        level=level,
        fmt="[%(levelname)s] [%(asctime)s] [%(name)s] %(message)s",
        level_styles=LEVEL_STYLES,
        field_styles=FIELD_STYLES)

    return logger


def parse_parameters():
    parser = argparse.ArgumentParser('dompare')
    parser.add_argument('dir1',
                        help="Path to the first directory")
    parser.add_argument('dir2',
                        help="Path to the second directory")
    parser.add_argument('--host',
                        type=str,
                        default='localhost',
                        help="host to bind")
    parser.add_argument('--port',
                        type=str,
                        default=5140,
                        help="port to listen")
    parser.add_argument('--verbose',
                        action='store_true',
                        help='Show detailed information')
    parser.add_argument('--exclude',
                        type=str,
                        nargs='+',
                        help='Ignore listed directories when diff')

    return parser.parse_args()


def diff_two_files(path1, path2, root_html_path):
    content1 = ''
    content2 = ''
    with open(path1, encoding='utf-8') as f:
        content1 = f.readlines()
    with open(path2, encoding='utf-8') as f:
        content2 = f.readlines()

    hd = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
    diff_content = hd.make_file(content1, content2, fromdesc=path1, todesc=path2, context=True)
    diff_content = remove_legends(diff_content)

    if 'No Differences Found' not in diff_content:
        with open(root_html_path.name, 'a+') as f:
            f.write(diff_content)
            f.close()



def diff_two_directories(logger, dir1, dir2, tmp_file, exclude):
    paths = os.listdir(dir1)

    if exclude is not None:
        exclude += ['.git']
    else:
        exclude = ['.git']

    for ex in exclude:
        if ex in paths:
            logger.debug('Ignore {}'.format(ex))
            paths.remove(ex)

    for path in paths:
        path1 = os.path.join(dir1, path)
        path2 = os.path.join(dir2, path)

        if os.path.isdir(path1) and not path1.startswith('.'):
            logger.debug('Processing dir {}'.format(path1))
            diff_two_directories(logger, path1, path2, tmp_file, exclude)

        elif is_binary(path1):
            logger.debug('Ignore binary file {}'.format(path1))
            continue

        elif not os.path.exists(os.path.join(dir2, path)):
            logger.debug('Ignore single file (no same name file in dir2) {}'.format(path1))
            continue

        else:
            logger.debug('Compare {} and {}'.format(path1, path2))
            diff_two_files(os.path.join(dir1, path), os.path.join(dir2, path), tmp_file)


def remove_legends(content):
    """ Remove redundant legends """
    content = content.replace('summary="Legends"', 'summary="Legends" style="display:none"')
    return content

def add_last_legends(tmp_file):
    """ Add legends at the end of diff content. """
    with open(tmp_file.name) as f:
        content = f.read()

    ptn = 'style="display:none"'
    pos = content.rfind(ptn)
    content = content[:pos] + content[pos+len(ptn):]

    with open(tmp_file.name, 'w') as f:
        f.write(content)


def run_http_server(logger, tmp_dir, host, port):
    logger.debug('Run http.server in dir: {}, host: {}:{}'.format(tmp_dir, host, port))
    os.chdir(tmp_dir)
    httpd = HTTPServer((host, int(port)), SimpleHTTPRequestHandler)
    httpd.serve_forever()


def main():
    args = parse_parameters()

    tmp_file = tempfile.NamedTemporaryFile(prefix='dompare-', suffix='.html', delete=False)
    tmp_dir = os.path.dirname(tmp_file.name)

    logger = create_logger(args.verbose)

    try:
        diff_two_directories(logger, args.dir1, args.dir2, tmp_file, args.exclude)
        add_last_legends(tmp_file)
        url = 'http://{}:{}/{}'.format(args.host, args.port, os.path.basename(tmp_file.name))
        logger.info('Compare finished. Please visit {} to see diff file (Press Ctrl-C to stop)'.format(url))
        run_http_server(logger, tmp_dir, args.host, args.port)
    finally:
        tmp_file.close()
        os.remove(tmp_file.name)



if __name__ == '__main__':
    main()
