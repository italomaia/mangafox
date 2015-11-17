#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import os
import sys
import lxml.html
import werkzeug

import urllib
from urllib2 import urlopen

# adding current dir to path (makes lookups easier)
dirname = os.path.abspath(os.path.dirname('.'))
sys.path.insert(0, dirname)

base_url = 'http://mangafox.me/'


def download_page(url, folder_name):
    handle = lxml.html.parse(url)

    for src in handle.xpath("//img[@id='image']/@src"):
        basename = os.path.basename(src)
        safe_basename = werkzeug.utils.secure_filename(basename)
        filename = os.path.join(folder_name, safe_basename)
        filename = os.path.abspath(filename)

        print u'writing %s' % filename

        if not os.path.exists(filename):
            data = urlopen(src).read()

            with open(filename, 'w') as file:
                file.write(data)
        else:
            print filename, 'exists. Skip.'


def download_chapter(chapter, folder_name):
    """
    Grabs all images from a chapter and writes them down to filesystem.

    """

    folder_name = werkzeug.utils.secure_filename(folder_name)

    # if the folder does not exist ...
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    handle = lxml.html.parse(chapter['href'])

    for value in handle.xpath("//select[@class='m']/option/@value"):
        value = int(value)
        url = re.sub(r'\d+\.html', '%d.html' % value, chapter['href'])
        download_page(url, folder_name)


def link_to_chapter(r):
    return {'name': r.text, 'href': r.attrib['href']}


def load_chapters(url):
    """
    Loads all chapters from a manga comic and returns a list for dictionaries
    with related data.

    """
    handle = lxml.html.parse(url)
    return [link_to_chapter(r) for r in handle.xpath("//*[@class='chlist']//a[@class!='edit']")]


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


def show_command(comic_url):
    '''
    prints all avaiable chapters

    '''
    chapters = load_chapters(comic_url)
    for i, chap in enumerate(chapters):
        print "%02d" % i, ' : ', chap['name']
    exit(0)


def download_command(url, args, enumerate_ch=False):
    """
    Downloads all asked chapters.
    Valid input formats:
    0,1,2 - downloads chapter 0, 1 and 2
    0-2 - downloads chapter 0, 1 and 2
    0-2,4 - downloads chapter 0, 1, 2 and 4

    """
    chapters = load_chapters(url)
    chapters.reverse()

    folder_name_fn = lambda index, chapter: chapter['name']

    if enumerate_ch:
        folder_name_fn = lambda index, chapter: '%03d' % index

    if args:
        for arg in args:
            for index in arg_to_list(arg):
                chapter = chapters[index]
                download_chapter(chapter, folder_name_fn(index, chapter))

    elif raw_input('Download all chapters? (y/n)\n') == 'y':
        for index, chapter in enumerate(chapters):
            download_chapter(chapter, folder_name_fn(index, chapter))
    else:
        print('nothing to download')

def search_command(name):
    full_url = 'http://www.mangafox.me/search.php?name_method=cw&name=%(name)s&type=&author_method=cw&author=&artist_method=cw&artist=&genres[Action]=0&genres[Adult]=0&genres[Adventure]=0&genres[Comedy]=0&genres[Doujinshi]=0&genres[Drama]=0&genres[Ecchi]=0&genres[Fantasy]=0&genres[Gender+Bender]=0&genres[Harem]=0&genres[Historical]=0&genres[Horror]=0&genres[Josei]=0&genres[Martial+Arts]=0&genres[Mature]=0&genres[Mecha]=0&genres[Mystery]=0&genres[One+Shot]=0&genres[Psychological]=0&genres[Romance]=0&genres[School+Life]=0&genres[Sci-fi]=0&genres[Seinen]=0&genres[Shoujo]=0&genres[Shoujo+Ai]=0&genres[Shounen]=0&genres[Shounen+Ai]=0&genres[Slice+of+Life]=0&genres[Smut]=0&genres[Sports]=0&genres[Supernatural]=0&genres[Tragedy]=0&genres[Webtoons]=0&genres[Yaoi]=0&genres[Yuri]=0&released_method=eq&released=&rating_method=eq&rating=&is_completed=&advopts=1'

    data = urlopen(full_url % {'name': urllib.quote(name)}).read()

    handle = lxml.html.fromstring(data)
    results = list()

    for link in handle.xpath('//td/a'):
        results.append({
            'url': link.attrib['href'],
            'name': link.text
        })

    if len(results):
        print ""
        for manga in results:
            for key, value in manga.items():
                print "%s: %s" % (key, value)
            print ""
    else:
        print 'No results found'


if __name__=="__main__":
    comic_uri = None

    import argparse
    parser = argparse.ArgumentParser(description='MangaFox script')
    parser.add_argument('url', type=str, nargs='?', help='URL to comic')
    parser.add_argument('-d', '--download', type=str, nargs='*')
    parser.add_argument('-f', '--find', type=str, help='Search for mangas in the database')
    parser.add_argument('-s', '--show', action='store_true')
    parser.add_argument('-n', '--enumerate', action='store_true')
    args = parser.parse_args()

    if args.find:
        search_command(args.find)
    elif args.url:
        url = args.url
        url += ('?' in url and '&' or '?')+ 'no_warning=1'

        if args.download:
            download_command(url, args.download, args.enumerate)
        elif args.show:
            show_command(url)
