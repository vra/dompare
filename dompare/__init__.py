import argparse
import difflib
import importlib
import os
import subprocess
import sys
import tempfile

from binaryornot.check import is_binary


def parse_parameters():
    parser = argparse.ArgumentParser('A program to diff two directories recursively')
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

    return parser.parse_args()


def diff_two_files(path1, path2, root_html_path):
    content1 = ''
    content2 = ''
    with open(path1) as f:
        content1 = f.readlines()
    with open(path2) as f:
        content2 = f.readlines()

    hd = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
    diff_content = hd.make_file(content1, content2, fromdesc=path1, todesc=path2, context=True)

    if 'No Differences Found' not in diff_content:
        with open(root_html_path.name, 'a+') as f:
            f.write(diff_content)



def diff_two_directories(dir1, dir2, tmp_file):
    paths = os.listdir(dir1)
    if '.git' in paths: paths.remove('.git')
    for path in paths:
        if os.path.isdir(os.path.join(dir1, path)) and not os.path.join(dir1, path).startswith('.'):
            diff_two_directories(os.path.join(dir1, path), os.path.join(dir2, path), tmp_file)
        elif is_binary(os.path.join(dir1, path)):
            continue
        elif not os.path.exists(os.path.join(dir2, path)):
            continue
        else:
            diff_two_files(os.path.join(dir1, path), os.path.join(dir2, path), tmp_file)



def run_http_server(tmp_dir, host, port):
    cmd = 'cd {} && python3 -m http.server --bind {} {}'.format(tmp_dir, host, port)
    os.system(cmd)


def main():
    tmp_file = tempfile.NamedTemporaryFile(prefix='dompare-', suffix='.html', dir='/tmp')
    tmp_dir = os.path.dirname(tmp_file.name)
    try:
        args = parse_parameters()
        diff_two_directories(args.dir1, args.dir2, tmp_file)
        url = 'http://{}:{}/{}'.format(args.host, args.port, os.path.basename(tmp_file.name))
        print('\nDone. Please visit {} to see diff file (Press Ctrl-C to stop)'.format(url))
        run_http_server(tmp_dir, args.host, args.port)
    finally:
        tmp_file.close()



if __name__ == '__main__':
    main()
