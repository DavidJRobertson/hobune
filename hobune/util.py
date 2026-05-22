import os
import urllib.parse


def no_traverse(path):
    return path.replace("/", "").replace("\\", "")


def quote_url(url):
    if os.path.sep == "\\":
        url = url.replace("\\", "/")
        url = url.replace("%5C", "/")
    return urllib.parse.quote(url).replace("%3A", ":")


def extract_ids_from_txt(filename):
    ids = set()
    if len(filename):
        with open(filename, "r") as f:
            for l in f:
                if len(l.strip()) >= 11:
                    ids.add(l.strip()[-11:])
    return ids
