# run resulting page locally with:
#   cd .\Projects\personal-page\
#   python -m http.server 8000

import os
import io
import re
from xml.etree import ElementTree
from datetime import date
from operator import itemgetter
import shutil

BASE_URL = 'https://wajib.space'
PAGE_DIRECTORY = os.path.join(os.path.dirname(os.getcwd()),'personal-page')
with open(os.path.join(os.getcwd(), 'navigation-bar.html'), 'r') as file:
    NAV_CONTENTS = file.read()

def wrap(tag, contents, attributes=None):
    attribute_string = ''.join(f' {key}="{attributes[key]}"' for key in attributes) if attributes else ''
    return ''.join([
        '<%s%s>' % (tag,attribute_string),
        ''.join(filter(lambda x: x != None, contents)),
        '</%s>' % tag
    ])

def headerElement(title = None):
    return wrap('head', [
        '<meta name="viewport" content="width=device-width, initial-scale=1.0"/>',
        '<script src="https://code.jquery.com/jquery-3.6.1.js"></script>',
        '<link rel="stylesheet" href="/default.css"/>',
        '<link rel="alternate" type="application/rss+xml" href="/rss.xml" title="RSS Feed"/>',
        f'<title>Wesley\'s Home Page{" - "+title if title else ""}</title>'
    ])

def bodyElement(title: str, content: str, created_at = None, updated_at = None):
    return wrap('body', [
	'<nav>',
        NAV_CONTENTS,
        '</nav>',
	mainElement(title, content, created_at, updated_at)
    ])

def mainElement(title: str, content: str, created_at = None, updated_at = None):
    return wrap('main', [
	('<h2>%s</h2>' % title) if title else '',
        content,
        wrap('span', [
            'published ',
            created_at.strftime('%b %d %Y')
        ], {'class': 'post_metadata'}) if created_at else '',
        '<br/>'+wrap('span', [
            'updated ',
            updated_at.strftime('%b %d %Y'),
        ], {'class': 'post_metadata'}) if (updated_at and created_at != updated_at) else ''
    ])

def generatePost(filename,filepath):
    try:
        source = ElementTree.parse(filepath)
    except ElementTree.ParseError as err:
        print(f'parse error in {filename}: {err}')
        return None
    published = False
    for child in source.getroot():
        if child.tag == 'title':
            title = child.text
        elif child.tag == 'description':
            description = child.text
        elif child.tag == 'html_content':
            content = ""
            for subchild in child:
                content += ElementTree.tostring(subchild, encoding="unicode")
        elif child.tag == 'published':
            if child.text == 'true':
                published = True
        elif child.tag == 'created_at':
            year,month,day = map(int,child.text.split('-'))
            created_at = date(year,month,day)
        elif child.tag == 'updated_at':
            year,month,day = map(int,child.text.split('-'))
            updated_at = date(year,month,day)
        elif child.tag == 'tags':
            tag_names = []
            for subchild in child:
                if subchild.tag == 'tag':
                    tag_names += [subchild.text]
    filename_without_ext = re.sub(r'\.xml$','',filename)
    if published:
        post_directory = os.path.join(PAGE_DIRECTORY,'posts',filename_without_ext)
        outfilepath = os.path.join(post_directory,'index.html')
        if not os.path.isdir(post_directory):
            os.mkdir(post_directory)
        clean_and_write(
            wrap('html',[
                headerElement(title),
                bodyElement(title, content, created_at, updated_at)
            ], {'lang': 'en-US'}),
            os.path.join(PAGE_DIRECTORY,'posts',filename_without_ext,'index.html'),
            'webpage'
        )
    return {
        'title': title,
        'description': description,
        'link': f'{BASE_URL}/posts/{filename_without_ext}',
        'published': published,
        'pagename': filename_without_ext,
        'created_at': created_at,
        'updated_at': updated_at,
        'tags': tag_names
    }

def generateRSS(items):
    channel_tag = wrap('channel', [
        '<title>Wesley\'s Home Page</title>',
        f'<link>{BASE_URL}</link>',
        '<description>My personal page where I post things I don\'t want anyone to see.</description>',
        '<language>en-US</language>',
        '<docs>https://www.rssboard.org/rss-specification</docs>',
        wrap('atom:link', [], {
            'href': f'{BASE_URL}/rss.xml',
            'rel': 'self',
            'type': 'application/rss+xml'
        })
    ] + [
        wrap('item',[
            wrap('title', [item['title']]),
            wrap('link', [item['link']]),
            wrap('description', [item['description']]),
            wrap('guid', [item['link']])
        ]) for item in items if item['published']
    ])
    return wrap('rss', [channel_tag], {
        'version': '2.0',
        'xmlns:atom': 'http://www.w3.org/2005/Atom'
    })

def generatePrimaryIndex(items, tags):
    return wrap('html',[
        headerElement(),
        bodyElement('',
            wrap('p','')+
            wrap('center',[wrap('a', tag, {'href': f'../tags/{tag}'}) for tag in tags])+
            wrap('ul',[
                wrap('li',[
                    wrap('a', item['title'], {'href': item['pagename']}),
                    (' - ' + item['description']),
                    ' ',
                    wrap('span', [
                        'published ',
                        item['created_at'].strftime('%b %d %Y'),
                        ', updated '+item['updated_at'].strftime('%b %d %Y') if item['created_at'] != item['updated_at'] else ''
                    ], {'class': 'post_metadata'})
                ]) for item in sorted(items,key=itemgetter('created_at'),reverse=True) if item['published']
            ])
        )
    ], {'lang': 'en-US'})
    
def generateTagIndex(items, tags, selected_tag):
    return wrap('html',[
        headerElement(),
        bodyElement('',
            wrap('p','')+
            wrap('center',[
                (wrap('b',tag) if tag == selected_tag else wrap('a', tag, {'href': f'../{tag}'})) for tag in tags
            ])+
            wrap('ul',[
                wrap('li',[
                    wrap('a', item['title'], {'href': f'../posts/{item['pagename']}'}),
                    (' - ' + item['description']),
                    ' ',
                    wrap('span', [
                        'published ',
                        item['created_at'].strftime('%b %d %Y'),
                        ', updated '+item['updated_at'].strftime('%b %d %Y') if item['created_at'] != item['updated_at'] else ''
                    ], {'class': 'post_metadata'})
                ]) for item in sorted(items,key=itemgetter('created_at'),reverse=True) if item['published'] and selected_tag in item['tags']
            ])
        )
    ], {'lang': 'en-US'})

def clean_and_write(xml_string: str, path: str, kind: str):
    assert(kind == 'rss' or kind == 'webpage')
    tree = ElementTree.parse(io.StringIO(xml_string))
    ElementTree.indent(tree.getroot())
    if kind == 'rss':
        ElementTree.register_namespace('atom','http://www.w3.org/2005/Atom')
        tree.write(path, method='xml')
    elif kind == 'webpage':
        tree.write(path, method='html')

items = []
tags = []
for file in os.listdir('posts'):
    filename = os.fsdecode(file)
    if filename.endswith('.xml'):
        filepath = os.path.join(os.getcwd(),'posts',filename)
        item = generatePost(filename, filepath)
        if item:
            items.append(item)
        if item['published']:
            tags = tags + item['tags']
tags = sorted(set(tags))
clean_and_write(
    generateRSS(items),
    os.path.join(PAGE_DIRECTORY,'rss.xml'),
    'rss'
)
clean_and_write(
    generatePrimaryIndex(items, tags),
    os.path.join(PAGE_DIRECTORY,'posts','index.html'),
    'webpage'
)
for tag in tags:
    tag_directory = os.path.join(PAGE_DIRECTORY,'tags',tag)
    if not os.path.isdir(tag_directory):
        os.mkdir(tag_directory)
    clean_and_write(
        generateTagIndex(items, tags, tag),
        os.path.join(tag_directory,'index.html'),
        'webpage'
    )
shutil.copy(
    os.path.join(os.getcwd(), 'default.css'),
    os.path.join(PAGE_DIRECTORY, 'default.css')
)
