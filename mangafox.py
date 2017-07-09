#!/usr/bin/env python
# coding:utf-8
import re
import os
import sys
from urllib.parse import urlparse
import requests
import werkzeug
from parsel import Selector

import urllib.parse
from collections import OrderedDict as odict

# adding current dir to path (makes lookups easier)
dirname = os.path.abspath(os.path.dirname('.'))
sys.path.insert(0, dirname)

domain = 'http://mangafox.me/'
opt_prefix = ''


class InputParser:
    pass


class QueryInputParser(InputParser):
    pass


class DownloadInputParser(InputParser):
    pass


class Command:
    pass


class Search(Command):
    REQUEST_BODY = {
        'advopts': '1',
        'artist': '',
        'artist_method': 'cw',
        'author': '',
        'author_method': 'cw',
        'genres[Action]': '0',
        'genres[Adult]': '0',
        'genres[Adventure]': '0',
        'genres[Comedy]': '0',
        'genres[Doujinshi]': '0',
        'genres[Drama]': '0',
        'genres[Ecchi]': '0',
        'genres[Fantasy]': '0',
        'genres[Gender+Bender]': '0',
        'genres[Harem]': '0',
        'genres[Historical]': '0',
        'genres[Horror]': '0',
        'genres[Josei]': '0',
        'genres[Martial+Arts]': '0',
        'genres[Mature]': '0',
        'genres[Mecha]': '0',
        'genres[Mystery]': '0',
        'genres[One+Shot]': '0',
        'genres[Psychological]': '0',
        'genres[Romance]': '0',
        'genres[School+Life]': '0',
        'genres[Sci-fi]': '0',
        'genres[Seinen]': '0',
        'genres[Shoujo+Ai]': '0',
        'genres[Shoujo]': '0',
        'genres[Shounen+Ai]': '0',
        'genres[Shounen]': '0',
        'genres[Slice+of+Life]': '0',
        'genres[Smut]': '0',
        'genres[Sports]': '0',
        'genres[Supernatural]': '0',
        'genres[Tragedy]': '0',
        'genres[Webtoons]': '0',
        'genres[Yaoi]': '0',
        'genres[Yuri]': '0',
        'is_completed': '',
        'name': '',  # required
        'name_method': 'cw',
        'rating': '',
        'rating_method': 'eq',
        'released': '',
        'released_method': 'eq',
        'type': ''
    }

    input_parser = QueryInputParser()

    def __init__(self, args):
        self.input_parser.add_args(args)

    def run(self, arg):
        pass

    def request(self):

        for arg in self.input_parser:
            self.run(arg)


def download_page(src, folder_name, index):
    parsed = urlparse(src)
    name, ext = os.path.splitext(parsed.path)
    filename = '%03d%s' % (index, ext)
    filename = werkzeug.utils.secure_filename(filename)
    filename = os.path.join(folder_name, filename)
    filename = os.path.abspath(filename)

    # file is not there or has a invalid size ...
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        data = requests.get(src).content

        with open(filename, 'wb') as file:
            file.write(data)

        print('{0} written.'.format(filename))
    else:
        print('{0} exists. Skipping.'.format(filename))


def download_chapter(chapter, folder_name):
    """
    Grabs all images from a chapter and writes them down to filesystem.

    :param chapter: chapter info dict
    """
    folder_name = (opt_prefix + '_' + folder_name)\
        if opt_prefix else folder_name

    chapter_href = chapter['href']
    base = os.path.dirname(chapter_href)
    folder_name = werkzeug.utils.secure_filename(folder_name)

    # if the folder does not exist ...
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    index = 0
    resp = requests.get(chapter_href)

    while resp.status_code == 200:
        sel = Selector(resp.text)
        src = sel.css('#image::attr(src)').extract_first()

        if src is None:
            print('src not found')
            break
        else:
            index += 1
            download_page(src, folder_name, index)
            next_page_path = sel.css('#viewer a::attr(href)').extract_first()

            if next_page_path is None:
                print('next page path not found')
                break
            else:
                resp = requests.get(os.path.join(base, next_page_path))


def hel_to_chapter(el):
    """
    Transforms an parsel element into a chapter dict.

    :param el: sel element
    :return: chapter's name, href and title
    :rtype: dict
    """
    return dict(
        name=el.css('a::text').extract_first(),
        href=el.css('a::attr(href)').extract_first(),
        title=el.css('span::text').extract_first()
    )


def load_chapters(url):
    """
    Loads all chapters from a manga comic and returns a list for dictionaries
    with related data.

    :return: chapter list in asc order
    """
    text = requests.get(url).text
    sel = Selector(text)
    hel_gen = sel.css(".chlist h3, .chlist h4")
    chapter_gen = map(hel_to_chapter, hel_gen)
    available_chapter_gen = filter(lambda v: v['href'], chapter_gen)
    return reversed(list(available_chapter_gen))


def arg_to_list(arg):
    """
    Converts a string in the format 'number|number[-number]' to a range of
    numbers. If separated by comma, all expressions are evaluated individually.
    Returns `Set`

    >>> arg_to_list('1')
    set([1])
    >>> arg_to_list('1-10')
    set(range(1-11))
    >>> arg_to_list('1,2,5,8-10')
    set([1,2,5,8,9,10])

    """
    rset = set()
    args = arg.split(',')
    num_c = re.compile(r'^\d+$')
    list_c = re.compile(r'^(\d+)\-(\d+)$')
    for bit in args:
        if num_c.match(bit):
            rset.add(int(bit))
        elif list_c.match(bit):
            m = list_c.match(bit)
            l, u = m.groups()
            rset.update(range(int(l), int(u) + 1))
    return rset


def show_command(name):
    """
    prints all avaiable chapters

    """
    url = _make_manga_url(name)
    chapters = load_chapters(url)
    line_template = "{index:^7s} :: {name:30s} :: {title}"
    header = line_template.format(index='Index', name='Chapter', title='Title')
    print(header + '\n')
    for index, chapter in enumerate(chapters):
        print(line_template.format(
            index='{:03d}'.format(index),
            name=chapter['name'][:30],
            title=chapter['title'] or ''
        ))


def make_folder_name(index, chapter):
    return chapter['name']


def make_folder_name_enum(index, chapter):
    return 'ch%03d' % index


def download_command(name, args):
    """
    Downloads all asked chapters.
    Valid input formats:
    0,1,2 - downloads chapter 0, 1 and 2
    0-2 - downloads chapter 0, 1 and 2
    0-2,4 - downloads chapter 0, 1, 2 and 4

    """
    url = _make_manga_url(name)
    chapters = load_chapters(url)
    folder_name_fn = make_folder_name_enum

    for arg in args:
        if arg == 'all':
            if input('Download all chapters (y/n)? ') == 'y':
                for index, chapter in enumerate(chapters):
                    folder_name = folder_name_fn(index, chapter)
                    download_chapter(chapter, folder_name)
        else:
            # force evaluation
            chapters = tuple(chapters)
            for index in arg_to_list(arg):
                chapter = chapters[index]  # dict
                folder_name = folder_name_fn(index, chapter)
                download_chapter(chapter, folder_name)


def search_command(value):
    """
    Search mangafox by your desired manga.

    :param value:
    """
    url = "{domain}/search.php?".format(domain=domain)
    quote = urllib.parse.quote(value)
    query = {
        'name': quote,
        'name_method': 'cw',
        'author': '',
        'author_method': 'cw',
        'artist': '',
        'artist_method': 'cw',
        'is_complete': '',
        'type': '',
        'advopts': '1',
        'rating': '',
        'rating_method': 'eq',
        'released': '',
        'released_method': 'eq',
        'genres[Sci-fi]': '0',
        'genres[Horror]': '0',
        'genres[Sports]': '0',
        'genres[Action]': '0',
        'genres[Shoujo Ai]#': '0',
        'genres[Drama]': '0',
        'genres[Fantasy]': '0',
        'genres[Mystery]': '0',
        'genres[Gender Bender]': '0',
        'genres[One Shot]': '0',
        'genres[Psychological]': '0',
        'genres[Tragedy]': '0',
        'genres[Historical]': '0',
        'genres[Mecha]': '0',
        'genres[Yuri]': '0',
        'genres[Seinen]': '0',
        'genres[Adult]': '0',
        'genres[Slice of Life]': '0',
        'genres[Doujinshi]': '0',
        'genres[Romance]': '0',
        'genres[School Life]': '0',
        'genres[Comedy]': '0',
        'genres[Shoujo]': '0',
        'genres[Ecchi]': '0',
        '#genres[Harem]': '0',
        'genres[Smut]': '0',
        'genres[Yaoi]': '0',
        'genres[Shounen Ai]': '0',
        'genres[Martial Arts]': '0',
        'genres[Josei]': '0',
        'genres[Shounen]': '0',
        'genres[Mature]': '0',
        'genres[Webtoons]': '0',
        'genres[Supernatural]': '0',
        'genres[Adventure]': '0',
    }
    url += urllib.parse.urlencode(query)

    try:
        data = requests.get(url).text
    except urllib.error.URLError:
        # mangafox requires a 5 seconds delay
        # between searches
        import time
        time.sleep(5)
        data = requests.get(url).text

    sel = Selector(data)
    results = list()

    for div in sel.css('#mangalist .list li div'):
        manga_url = div.css('::attr(href)').extract_first()
        name = manga_url[7:].split('/')[2]
        results.append(odict([
            ('title', div.css('::text').extract_first()),
            ('name', "%s (use for download)" % name),
            ('url', manga_url),
        ]))

    if len(results):
        print("")
        for manga in results:
            for key, value in manga.items():
                print("%s: %s" % (key, value))
            print("")
    else:
        print('No results found')


def _make_manga_url(name):
    """Construct a valid manga url form mangafox."""
    return "{domain}manga/{name}/?no_warning=1"\
        .format(domain=domain, name=name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='''MangaFox script

Usage:

mangafox.py -h  # diplays options
mangafox.py -f "one piece"  # is one piece available?
mangafox.py -f "one piece" | mangafox.py -s  # show info on what you find
# download everything that you find
mangafox.py -f "one piece" | mangafox.py -d
# download first three chapters of what you find
mangafox.py -f "one piece" | mangafox.py -d 1,2,3
''')
    parser.add_argument(
        'name', type=str, nargs='?',
        help='comic name (ex: boku_no_hero_academia)')
    parser.add_argument('-d', '--download', type=str, nargs=1)
    parser.add_argument(
        '-f', '--find', type=str, help='Search for mangas in the database')
    parser.add_argument(
        '-s', '--show', action='store_true', help='Show manga information')
    parser.add_argument(
        '-p', '--prefix', default='', help='chapter prefix')
    args = parser.parse_args()

    global opt_prefix
    opt_prefix = args.prefix

    if args.find:
        search_command(args.find)
    elif args.name and args.download:
        download_command(args.name, args.download)
    elif args.name and args.show:
        show_command(args.name)
