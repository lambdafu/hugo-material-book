#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Generate PDF from markdown.  Requires pandoc, a recent
# python-pandocfilters and TeX with following packages:
# texlive-babel-german, texlive-inconsolata, texlive-opensans, texlive-mdframed,
# texlive-hyphen-german, texlive-glossaries-german
# Later maybe also:
# texlive-xelatex-bin, texlive-mathspec, texlive-euenc, texlive-polyglossia,

import sys
import os
import argparse
from subprocess import check_output
import json
import re

from pandocfilters import toJSONFilter, walk, stringify
from pandocfilters import elt, Para, Plain, Str, Header, Image, RawInline

MetaString = elt('MetaString', 1)
MetaList = elt('MetaList', 1)

def RawTexPara(tex):
    return Para([RawInline("tex", tex)])

def BookPart(title):
    titlestr = stringify(title)
    partcmd = r'\part{%s}' % titlestr
    return RawTexPara(partcmd)

RE_HEADER_REF = re.compile(r'\W+', re.UNICODE)
def MakeHeader(level, title):
    titlestr = stringify(title)
    ref = RE_HEADER_REF.sub('-', titlestr)
    ref = ref.rstrip('-').lower()
    return Header(level, [ref, [], []], [Str(titlestr)])

IMAGE_PATH = os.path.dirname(os.path.abspath(__file__))
PANDOC = 'pandoc'
LC = 'en'
PAPERSIZE = 'a4'
TOC = True
NUMBERSECTIONS = True

def to_json(args, filename):
    data = check_output([args.pandoc, "-t", "json", filename])
    return json.loads(data)

# Generic filter
def fix_header_ref(key, value, format, meta):
    if key == 'Header':
        level, ref, content = value
        # Hugo removes . and - from header before creating the anchor, while pandoc does not.
        # This can create duplicated hyphens, which we replace here.
        ref_label = ref[0]
        ref_label = RE_HEADER_REF.sub("-", ref_label)
        ref_label = ref_label.rstrip("-")
        ref = [ref_label] + ref[1:]
        return Header(level, ref, content)
    return None

def fix_image_ref(key, value, format, meta):
    if key == 'Image':
        image_desc = value[-1]
        image_path = image_desc[0]
        # Replace leading '/' with relative path to images/.
        image_path = os.path.join(IMAGE_PATH, "static", image_path[1:])
        args = value[:-1] + [ [image_path] + image_desc[1:] ]
        return Image(*args)
    return None

RE_NOTE = re.compile(r'''\s*([a-z]+)(?:\s+title\s*=\s*"([^"]*)")?\s*''')
RE_NOTE_END = re.compile(r'''\s*/\s*([a-z]+)\s*''')
fix_notes_buffer = None
def fix_notes(key, value, format, meta):
    global fix_notes_buffer
    if key == 'Str' and value == '{{<':
        fix_notes_buffer = ""
        return Str("")
    elif key == 'Str' and value == '>}}':
        if fix_notes_buffer is not None:
            buffer = fix_notes_buffer
            fix_notes_buffer = None

            mtb = RE_NOTE.match(buffer)
            mte = RE_NOTE_END.match(buffer)
            if mtb is not None:
                note_type, label = mtb.groups()
                if label is None:
                    return RawInline('tex', r'\begin{%s}' % note_type)
                else:
                    return RawInline('tex', r'\begin{%s}[frametitle=%s]' % (note_type, label))
            elif mte is not None:
                note_type = mte.groups()
                return RawInline('tex', r'\end{%s}' % note_type)
            else:
                return Str("{{< %s >}}" % buffer)
            return ret
    elif fix_notes_buffer is not None:
        fix_notes_buffer += stringify([{'t': key, 'c': value}])
        return Str("")
    return None

def book_add_metadata(args, doc, documentclass="book"):
    meta = doc[0]['unMeta']

    meta['documentclass'] = MetaString(documentclass)

    meta['lang'] = MetaString(args.lang)
    meta['papersize'] = MetaString(args.papersize)
    meta['toc'] = MetaString(str(args.toc))
    meta['numbersections'] = MetaString(str(args.number_sections))

    if args.author is not None:
        meta['author'] = MetaString(args.author)

    meta['header-includes'] = MetaList([
        MetaString(r'\usepackage{inconsolata}'),
        MetaString(r'\usepackage[default]{opensans}'),
        MetaString(r'\usepackage[xcolor]{mdframed}'),
        #    MetaString(r'\newmdenv[topline=false,bottomline=false,linecolor=red,linewidth=3pt,skipabove=\topskip,skipbelow=\topskip]{warning}'),
        MetaString(r'\newmdenv[linewidth=0pt,skipabove=\topskip,skipbelow=\topskip,backgroundcolor=red!10]{warning}'),
        MetaString(r'\newmdenv[linewidth=0pt,skipabove=\topskip,skipbelow=\topskip,backgroundcolor=blue!10]{note}'),
        MetaString(r'\DeclareUnicodeCharacter{2192}{$\rightarrow$}'), # Better to use latex-engine=xelatex, but it's broken on Fedora with German
    ])
    doc[0]['unMeta'] = meta
    return doc

def book_add_part(args, doc, part):
    meta = part[0]['unMeta']
    part = BookPart(meta.get('title', 'MISSING TITLE'))
    doc[1].append(part)
    return doc

def chapter_header_level(key, value, format, meta):
    if key == 'Header':
        level, ref, content = value
        # Move all header elements one up, because material doc theme reserves h1 for the theme and starts with h2.
        level = level - 1
        return Header(level, ref, content)
    return None

def book_add_chapter(args, doc, chapter):
    meta = chapter[0]['unMeta']
    header = meta.get('title', MetaString('MISSING TITLE'))
    header = MakeHeader(0, header)
    doc[1].append(header)

    content = chapter[1]

    actions = [chapter_header_level, fix_header_ref, fix_image_ref, fix_notes]
    content = reduce(lambda x, action: walk(x, action, format, meta), actions, content)
    doc[1].extend(content)
    return doc

def article_add_chapter(args, doc, chapter):
    meta = chapter[0]['unMeta']
    content = chapter[1]

    actions = [chapter_header_level, fix_header_ref, fix_image_ref, fix_notes]
    content = reduce(lambda x, action: walk(x, action, format, meta), actions, content)
    doc[1].extend(content)
    return doc

def arg_parser():

    # In args.parts, we end up with a list of (part, chapters) tuples (first part may be None).
    class ChaptersAction(argparse.Action):
        def __init__(self, option_strings, dest, **kwargs):
            super(ChaptersAction, self).__init__(option_strings, dest, **kwargs)
        def __call__(self, parser, namespace, values, option_string=None):
            parts = getattr(namespace, 'parts', None)
            if parts is None:
                parts = []
            parts.append((namespace.part, values))
            namespace.part = None
            namespace.chapters = None
            setattr(namespace, 'parts', parts)

    parser = argparse.ArgumentParser(description='generate a book from multiple pandoc documents')
    parser.add_argument('--pandoc', metavar='FILE', type=str, default=PANDOC, help='path to pandoc binary (default: %s)' % PANDOC)

    parser.add_argument('--lang', metavar='LC', type=str, default=LC, help='language code (default: %s)' % LC)
    parser.add_argument('--papersize', metavar='FORMAT', type=str, default=PAPERSIZE, help='papersize (default: %s)' % PAPERSIZE)
    parser.add_argument('--toc', metavar='BOOL', type=bool, default=TOC, help='toc (default: %s)' % TOC)
    parser.add_argument('--number-sections', metavar='BOOL', type=bool, default=NUMBERSECTIONS, help='number sections (default: %s)' % NUMBERSECTIONS)

    parser.add_argument('--author', metavar='STRING', type=str, help='document author')

    parser.add_argument('--book', metavar='FILE', type=str, help='start a book with this file')
    parser.add_argument('--part', metavar='FILE', type=str, help='start a new part in a multi-volume book')
    parser.add_argument('--chapters', metavar='FILE', type=str, action=ChaptersAction, nargs='*', help='chapters in the book or part')

    parser.add_argument('--article', metavar='FILE', type=str, help='start an article with this file')
    args = parser.parse_args()
    # Normalize parts member.
    parts = getattr(args, 'parts', None)
    if parts is None:
        parts = []
    args.parts = parts

    # Prepare title and metadata.
    if args.book is not None:
        doc = to_json(args, args.book)
        book_add_metadata(args, doc)
        if len(doc[1]) > 0:
            # Add a silent chapter for the preambel.
            header = RawTexPara(r"\chapter*{%s}" % stringify(doc[0]['unMeta'].get('title', Str('Einleitung'))))
            doc[1].insert(0, header)

        for part, chapters in args.parts:
            if part is not None:
                part = to_json(args, part)
                book_add_part(args, doc, part)
                if len(part[1]) > 0:
                    # Add a silent chapter for the preambel.
                    header = RawTexPara(r"\chapter*{%s}" % stringify(part[0]['unMeta'].get('title', Str('Einleitung'))))
                    doc[1].append(header)
                    doc[1].extend(part[1])
            for chaptername in chapters:
                chapter = to_json(args, chaptername)
                book_add_chapter(args, doc, chapter)
    elif args.article is not None:
        doc = to_json(args, args.article)
        book_add_metadata(args, doc, documentclass="article")

        chapter = [doc[0], doc[1]]
        doc[1] = []
        article_add_chapter(args, doc, chapter)


    print ('%s' % json.dumps(doc))

if __name__ == '__main__':
    arg_parser()
