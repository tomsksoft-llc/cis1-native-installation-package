#!/usr/bin/env python3

import requests
import json
import argparse
import sys
import tarfile
import subprocess
import tempfile
import os

fname = 'cis-native-installation-package.tar.gz'

def load_releases(prereleases):
    response = requests.get('https://api.github.com/repos/tomsksoft-llc/cis1-native-installation-package/releases')
    releases = json.loads(response.text)
    releases = list(filter(lambda release:
                           release['draft'] == False,
                           releases))
    if prereleases != True:
        releases = list(filter(lambda release:
                               release['prerelease'] == False,
                               releases))
    return releases

def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def print_page(releases):
    i = 1
    for release in releases:
        print("{}) {} {}".format(i, release['tag_name'], release['name']))
        i += 1

def pick_release(releases):
    release_pages = list(divide_chunks(releases, 10))

    release = None
    page = 1
    while release is None:
        print_page(release_pages[page - 1])
        if page > 1:
            print("(b) for previous page")
        if page < len(release_pages):
            print("(n) for next page")
        c = input()
        if c == 'b' and page > 1:
            page -= 1
            continue
        if c == 'n' and page < len(release_pages):
            page += 1
            continue
        if int(c) in range(1, len(release_pages[page - 1])):
            release = release_pages[page - 1][int(c)]
            continue
        raise Exception('Incorrect input')

    return release

def download(directory, url, name):
    r = requests.get(
        url,
        stream=True,
        headers={'Accept': 'application/octet-stream'})

    if r.status_code == 200:
        with open(name, 'wb') as f:
            for chunk in r:
                f.write(chunk)

def unpack(output, input=fname):
    tar = tarfile.open(fname, "r:gz")
    tar.extractall(path = output)
    tar.close()

def main(argv = None):
    parser = argparse.ArgumentParser(
        description = 'Deploy cis core to given directory.')

    parser.add_argument(
        '--dir',
        type = str,
        required = True,
        help = 'installation directory.')

    parser.add_argument(
        '--prerelease',
        dest='prerelease',
        required = False,
        action='store_true',
        default = False,
        help = 'install prereleases too.')

    parser.add_argument(
        '--interactive',
        dest='interactive',
        required = False,
        action='store_true',
        default = False,
        help = 'choose release from list interactively.')

    parser.add_argument(
        '--archive',
        required = False,
        type = str,
        help = 'install from archive.')

    args = parser.parse_args()

    if args.archive == None:
        directory = tempfile.TemporaryDirectory()
        releases = load_releases(args.prerelease)
        release = pick_release(releases) if args.interactive else releases[0]
        for asset in release['assets']:
            download(directory, asset['url'], asset['name'])
        subprocess.run(["installer.py", "--dir", args.dir, "--archive", os.path.join(directory, fname)], check=True)
    else:
        unpack(output = args.dir)

if __name__ == "__main__":
    sys.exit(main())
