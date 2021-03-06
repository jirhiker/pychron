# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#========== standard library imports ==========
import glob
import os
import subprocess
from datetime import datetime


def view_file(p, application='Preview', logger=None):
    app_path = '/Applications/{}.app'.format(application)
    if not os.path.exists(app_path):
        app_path = '/Applications/Preview.app'

    try:
        subprocess.call(['open', '-a', app_path, p])
    except OSError:
        if logger:
            logger.debug('failed opening {} using {}'.format(p, app_path))
        subprocess.call(['open', p])


def ilist_directory2(root, extension=None, filtername=None, remove_extension=False):
    """
        uses glob
        root: directory to list
        extension: only return files of this file type e.g .txt or txt
                extension can be list, tuple or str

        return iterator
    """
    if filtername is None:
        filtername = ''

    def gen(gf):
        for p in glob.iglob(gf):
            p = os.path.basename(p)
            if remove_extension:
                p, _ = os.path.splitext(p)
            yield p

    gfilter = root
    if extension:
        if not isinstance(extension, (list, tuple)):
            extension = (extension, )

        for ext in extension:
            if not ext.startswith('.'):
                ext = '.{}'.format(ext)
            gfilter = '{}/{}*{}'.format(root, filtername, ext)
            # print gfilter
            for yi in gen(gfilter):
                yield yi
    else:
        for yi in gen(gfilter):
            yield yi


def list_directory2(root, extension=None, filtername=None, remove_extension=False):
    return list(ilist_directory2(root, extension, filtername, remove_extension))


def list_directory(p, extension=None, filtername=None, remove_extension=False):
    ds = []
    #if extension:

    #return any([path.endswith(ext) for ext in extension.split(',')])
    #else:
    #    def test(path):
    #        return True

    if os.path.isdir(p):
        ds = os.listdir(p)
        if extension is not None:
            def test(path):
                for ext in extension.split(','):
                    if path.endswith(ext):
                        return True

            ds = [pi for pi in ds
                  if test(pi)]
        if filtername:
            ds = [pi for pi in ds if pi.startswith(filtername)]

    if remove_extension:
        ds = [os.path.splitext(pi)[0] for pi in ds]
    return ds


def add_extension(p, ext='.txt'):
    if not p.endswith(ext):
        # p += ext
        p = '{}{}'.format(p, ext)
    return p


def remove_extension(p):
    h, _ = os.path.splitext(p)
    return h


def unique_dir(root, base):
    p = os.path.join(root, '{}001'.format(base))
    i = 2
    while os.path.exists(p):
        p = os.path.join(root, '{}{:03n}'.format(base, i))
        i += 1

    os.mkdir(p)

    return p


def unique_date_path(root, base, extension='.txt'):
    """
        make a unique path with the a timestamp appended
        e.g foo_11-01-2012-001
    """
    base = '{}_{}'.format(base, datetime.now().strftime('%m-%d-%Y'))
    p, _ = unique_path2(root, base, extension)
    return p


def unique_path2(root, base, extension='.txt'):
    """
        unique_path suffers from the fact that it starts at 001.
        this is a problem for log files because the logs are periodically archived which means
        low paths are removed.

        unique_path2 solves this by finding the max path then incrementing by 1
    """
    # find the max path in the root directory
    basename = '{}-*{}'.format(base, extension)
    cnt = 0
    for p in glob.iglob(os.path.join(root, basename)):
        p = os.path.basename(p)
        head, tail = os.path.splitext(p)
        cnt = max(int(head.split('-')[1]), cnt)

    cnt += 1
    p = os.path.join(root, '{}-{:03n}{}'.format(base, cnt, extension))
    return p, cnt


def unique_path(root, base, extension='.txt'):
    """

    """
    if extension:
        if '.' not in extension:
            extension = '.{}'.format(extension)
    else:
        extension = ''

    p = os.path.join(root, '{}-001{}'.format(base, extension))
    cnt = 1
    i = 2
    while os.path.isfile(p):
        p = os.path.join(root, '{}-{:03n}{}'.format(base, i, extension))
        i += 1
        cnt += 1

    return p, cnt


def to_bool(a):
    """
        a: a str or bool object

        if a is string
            'true', 't', 'yes', 'y', '1', 'ok' ==> True
            'false', 'f', 'no', 'n', '0' ==> False
    """

    if isinstance(a, bool):
        return a
    elif isinstance(a, (int, float)):
        return bool(a)

    tks = ['true', 't', 'yes', 'y', '1', 'ok']
    fks = ['false', 'f', 'no', 'n', '0']

    if a is not None:
        a = str(a).strip().lower()

    if a in tks:
        return True
    elif a in fks:
        return False


def parse_xy(p, delimiter=','):
    """
    """
    data = parse_file(p)
    if data:
        func = lambda i, data: [float(l.split(delimiter)[i]) for l in data]

        return func(0, data), func(1, data)


def commented_line(l):
    """
    """
    if l[:1] == '#':
        return True
    else:
        return False


def parse_file(p, delimiter=None, cast=None):
    """
        p: absolute path
        delimiter: str
        cast: callable. applied to each delimited field

    """
    if os.path.exists(p) and os.path.isfile(p):
        with open(p, 'U') as fp:
            r = filetolist(fp)
            if delimiter:
                if cast is None:
                    cast = str
                r = [map(cast, ri.split(delimiter)) for ri in r]

            return r


def parse_setupfile(p):
    """
    """

    fp = parse_file(p)
    if fp:
        return [line.split(',') for line in file]


def parse_canvasfile(p, kw):
    '''
    
    '''
    # kw=['origin','valvexy','valvewh','opencolor','closecolor']

    if os.path.exists(p) and os.path.isfile(p):
        with open(p, 'r') as fp:
            indices = {}
            i = 0
            f = filetolist(fp)
            count = 1
            for i in range(len(f)):
                if f[i][:1] == '!':
                    for k in kw:
                        if f[i][1:] == k:
                            i += 1
                            if k in indices:
                                k = k + str(count)
                                count += 1

                            indices[k] = f[i].split(',')

                            i += 1
                            break

            return indices


def pathtolist(p, **kw):
    """
        p: absolute path to file

        kw: same keyword arguments accepted by filetolist
        return: list
    """
    with open(p, 'r') as fp:
        return filetolist(fp, **kw)


def filetolist(f, commentchar='#'):
    """
        f: file-like object
        return list
    """

    def isNewLine(c):
        return c == chr(10) or c == chr(13)

    def test(li):
        cc = li[:1]
        return not (cc == commentchar or isNewLine(cc))

    r = (line for line in f if test(line))
    r = [line.split(commentchar)[0].strip() for line in r]
    # r = []
    #
    # for line in f:
    #     cc = line[:1]
    #     if not cc == commentchar and not isNewLine(cc):
    #         # l = line[:-1] if line[-1:] == '\n' else line
    #         # remove inline comments
    #         line = line.split('#')[0]
    #         r.append(line.strip())
    return r


def fileiter(fp, commentchar='#', strip=False):
    def isNewLine(c):
        return c in ('\r', '\n')

    def test(li):
        cc = li[:1]
        return not (cc == commentchar or isNewLine(cc))

    for line in fp:
        if test(line):
            if strip:
                line = line.strip()
            yield line

