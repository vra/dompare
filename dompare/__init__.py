"""A command line tool to diff two directories recursively."""
import argparse
import difflib
from http.server import HTTPServer, SimpleHTTPRequestHandler
import logging
import os
import sys
import tempfile

from binaryornot.check import is_binary
from loguru import logger


def is_binary_string(filename):
    with open(filename, "rb") as f:
        bytes = f.read(1024)
        textchars = bytearray(
            {7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F}
        )
        return bool(bytes.translate(None, textchars))


def is_binary_file(filename):
    with open(filename, "rb") as f:
        # Read the first 1024 bytes of the file
        data = f.read(1024)
        # Check for null bytes
        return b"\0" in data


def parse_parameters():
    parser = argparse.ArgumentParser("dompare")
    parser.add_argument("dir1", help="Path to the first directory")
    parser.add_argument("dir2", help="Path to the second directory")
    parser.add_argument("--host", type=str, default="localhost", help="host to bind")
    parser.add_argument("--port", type=str, default=5240, help="port to listen")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--exclude-dot",
        action="store_true",
        dest="exclude_dot",
        help="Ignore All hidden folders and files beginning with .",
    )
    parser.add_argument(
        "--show-same",
        action="store_true",
        dest="show_same",
        help="Show files that no difference in html file",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        type=str,
        nargs="+",
        help="Ignore listed directories when diff",
    )

    return parser.parse_args()


def detect_file_encoding(path):
    import chardet

    with open(path, "rb") as f:
        return chardet.detect(f.read())["encoding"]


def diff_two_files(path1, path2, root_html_path, show_same):
    content1 = ""
    content2 = ""
    try:
        with open(path1, encoding=detect_file_encoding(path1)) as f:
            content1 = f.readlines()
        with open(path2, encoding=detect_file_encoding(path2)) as f:
            content2 = f.readlines()
    except UnicodeDecodeError:
        logger.warning("Open file error: {}".format(path1))
        return

    hd = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
    diff_content = hd.make_file(
        content1, content2, fromdesc=path1, todesc=path2, context=True
    )
    diff_content = remove_legends(diff_content)

    need_write = True if show_same else "No Differences Found" not in diff_content
    if need_write:
        with open(root_html_path.name, "a+") as f:
            f.write(diff_content)
            f.close()


def diff_two_directories(dir1, dir2, tmp_file, exclude, exclude_dot, show_same):
    if exclude is not None:
        exclude += [".git"]
    else:
        exclude = [".git"]

    # Add comparsion betwen two files
    if os.path.isfile(dir1) and os.path.isfile(dir2):
        target_path = os.path.basename(dir1)
        target_path1 = os.path.basename(dir2)
        dir1 = os.path.dirname(dir1)
        dir2 = os.path.dirname(dir2)
        all_paths = os.listdir(dir1)
        for path in all_paths:
            if path != target_path:
                exclude.append(path)

        paths = [target_path]

    else:
        paths = os.listdir(dir1)
        if exclude_dot:
            paths = [path for path in paths if not path.startswith(".")]
        for ex in exclude:
            if ex in paths:
                logger.debug("Ignore {}".format(ex))
                paths.remove(ex)

    for path in paths:
        path1 = os.path.join(dir1, path)
        path2 = os.path.join(dir2, path)
        need_skip = False
        for ex in exclude:
            if ex in path1:
                need_skip = True
                break
            if ex in path1:
                need_skip = True
                break
        if need_skip:
            logger.debug("Ignore {}".format(path1))
            continue

        if os.path.isdir(path1):
            logger.debug("Processing dir {}".format(path1))
            diff_two_directories(
                path1, path2, tmp_file, exclude, exclude_dot, show_same
            )

        elif os.path.islink(path1):
            logger.debug("Ignore symlink file {}".format(path1))
            continue

        elif is_binary(path1) or is_binary_file(path1) or is_binary_string(path1):
            logger.debug("Ignore binary file {}".format(path1))
            continue

        elif not os.path.exists(os.path.join(dir2, path)):
            logger.debug(
                "Ignore single file (no same name file in dir2) {}".format(path1)
            )
            continue

        else:
            logger.debug("Compare {} and {}".format(path1, path2))
            diff_two_files(
                os.path.join(dir1, path), os.path.join(dir2, path), tmp_file, show_same
            )


def remove_legends(content):
    """Remove redundant legends"""
    content = content.replace(
        'summary="Legends"', 'summary="Legends" style="display:none"'
    )
    return content


def add_last_legends(tmp_file):
    """Add legends at the end of diff content."""
    with open(tmp_file.name) as f:
        content = f.read()

    ptn = 'style="display:none"'
    pos = content.rfind(ptn)
    content = content[:pos] + content[pos + len(ptn) :]

    if content == "":
        content = "No diff is found"

    with open(tmp_file.name, "w") as f:
        f.write(content)


def run_http_server(tmp_dir, host, port):
    logger.debug("Run http.server in dir: {}, host: {}:{}".format(tmp_dir, host, port))
    os.chdir(tmp_dir)
    httpd = HTTPServer((host, int(port)), SimpleHTTPRequestHandler)
    httpd.serve_forever()


def main():
    args = parse_parameters()

    logger.remove()
    if args.verbose:
        logger.add(sys.stdout, level="DEBUG")
    else:
        logger.add(sys.stdout, level="INFO")

    logger.info("Running, please wait...")
    out_dir1 = os.path.realpath(args.dir1)
    out_dir2 = os.path.realpath(args.dir2)

    assert os.path.exists(out_dir1), "path1 {} is not exist!".format(out_dir1)
    assert os.path.exists(out_dir2), "path2 {} is not exist!".format(out_dir2)

    tmp_file = tempfile.NamedTemporaryFile(
        prefix="dompare-", suffix=".html", delete=False
    )
    tmp_dir = os.path.dirname(tmp_file.name)

    try:
        diff_two_directories(
            out_dir1,
            out_dir2,
            tmp_file,
            args.exclude,
            args.exclude_dot,
            args.show_same,
        )
        add_last_legends(tmp_file)
        url = "http://{}:{}/{}".format(
            args.host, args.port, os.path.basename(tmp_file.name)
        )
        logger.info(
            "Compare finished. Please visit {} to see diff file (Press Ctrl-C to stop)".format(
                url
            )
        )
        run_http_server(tmp_dir, args.host, args.port)
    finally:
        tmp_file.close()
        os.remove(tmp_file.name)


if __name__ == "__main__":
    main()
