#!/usr/bin/env python
# coding:utf-8
import re
import os
import sys
from parsel import Selector
import requests
import werkzeug

import urllib.parse
from collections import OrderedDict as odict

# adding current dir to path (makes lookups easier)
dirname = os.path.abspath(os.path.dirname('.'))
sys.path.insert(0, dirname)

domain = 'http://mangafox.me/'


def download_page(url, folder_name):
    text = requests.get(url).text
    sel = Selector(text)

    for src in sel.css("img[id='image']::attr(src)").extract():
        basename = os.path.basename(src)
        safe_basename = werkzeug.utils.secure_filename(basename)
        filename = os.path.join(folder_name, safe_basename)
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

    """

    folder_name = werkzeug.utils.secure_filename(folder_name)

    # if the folder does not exist ...
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    text = requests.get(chapter['href']).text
    sel = Selector(text)

    for value in sel.css("select[class='m'] > option::attr(value)").extract():
        value = int(value)
        url = re.sub(r'\d+\.html', '%d.html' % value, chapter['href'])
        download_page(url, folder_name)


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
    available_chapter_gen = filter(lambda v: v['title'], chapter_gen)
    return reversed(list(available_chapter_gen))


def arg_to_list(arg):
    """
    Converts a string in the format 'number|number[-number]' to a range of numbers.
    If separated by comma, all expressions are evaluated individually.
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
            rset.update(range(int(l), int(u)+1))
    return rset


def show_command(name):
    """
    prints all avaiable chapters

    """
    url = make_manga_url(name)
    chapters = load_chapters(url)
    line_template = "{index:^7s} :: {name:30s} :: {title}"
    header = line_template.format(index='Index', name='Chapter', title='Title')
    print(header + '\n')
    for index, chapter in enumerate(chapters):
        print(line_template.format(
            index='{:03d}'.format(index),
            name=chapter['name'][:30],
            title=chapter['title']
        ))


def make_folder_name(index, chapter):
    return chapter['name']


def make_folder_name_enum(index, chapter):
    return '%03d' % index


def download_command(name, args, enumerate_ch=False):
    """
    Downloads all asked chapters.
    Valid input formats:
    0,1,2 - downloads chapter 0, 1 and 2
    0-2 - downloads chapter 0, 1 and 2
    0-2,4 - downloads chapter 0, 1, 2 and 4

    """
    url = make_manga_url(name)
    chapters = load_chapters(url)
    folder_name_fn = make_folder_name_enum if enumerate_ch \
        else make_folder_name 

    if args:
        for arg in args:
            # force evaluation
            chapters = tuple(chapters)

            for index in arg_to_list(arg):
                chapter = chapters[index]
                download_chapter(chapter, folder_name_fn(index, chapter))

    elif raw_input('Download all chapters? (y/n)\n') == 'y':
        for index, chapter in enumerate(chapters):
            download_chapter(chapter, folder_name_fn(index, chapter))
    else:
        print('nothing to download')


def search_command(value):
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

    for link in sel.css('td:first-child > a:first-child'):
        manga_url = link.css('::attr(href)').extract_first()
        name = manga_url[7:].split('/')[2]
        results.append(odict([
            ('title', link.css('::text').extract_first()),
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


def make_manga_url(name):
    return "{domain}manga/{name}/?no_warning=1".format(domain=domain, name=name)


if __name__ == "__main__":
    import argparse

    comic_uri = None

    parser = argparse.ArgumentParser(description='MangaFox script')
    parser.add_argument('name', type=str, nargs='?', help='comic name (ex: boku_no_hero_academia)')
    parser.add_argument('-d', '--download', type=str, nargs='*')
    parser.add_argument('-f', '--find', type=str, help='Search for mangas in the database')
    parser.add_argument('-s', '--show', action='store_true', help='Show manga information')
    parser.add_argument('-n', '--enumerate', action='store_true', help='List all pages')
    args = parser.parse_args()

    if args.find:
        search_command(args.find)
    elif args.name:
        name = args.name

        if args.download:
            download_command(name, args.download, args.enumerate)

        elif args.show:
            show_command(name)
