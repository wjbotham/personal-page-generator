import os
import io
import re
from xml.etree import ElementTree

BASE_URL = 'https://wajib.space'
PAGE_DIRECTORY = os.path.join(os.path.dirname(os.getcwd()),'personal-page')
with open(os.path.join(os.getcwd(), 'navigation-bar.html'), 'r') as file:
    NAV_CONTENTS = file.read()

def wrap(tag, contents, attributes=None):
    attribute_string = ''.join(f' {key}="{attributes[key]}"' for key in attributes) if attributes else ''
    return ''.join([
        '<%s%s>' % (tag,attribute_string),
        ''.join(contents),
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

def bodyElement(title: str, description: str, content: str):
    return wrap('body', [
	'<nav>',
        NAV_CONTENTS,
        '</nav>',
	mainElement(title, description, content)
    ])

def mainElement(title: str, description: str, content: str):
    return wrap('main', [
	('<h2>%s</h2>' % title) if title else '',
        ('<p>%s</p>' % description) if description else '',
        content
    ])

def generatePost(filename,filepath):
    source = ElementTree.parse(filepath)
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
    filename_without_ext = re.sub(r'\.xml$','',filename)
    if published:
        post_directory = os.path.join(PAGE_DIRECTORY,'posts',filename_without_ext)
        outfilepath = os.path.join(post_directory,'index.html')
        if not os.path.isdir(post_directory):
            os.mkdir(post_directory)
        clean_and_write(
            wrap('html',[
                headerElement(title),
                bodyElement(title, description, content)
            ], {'lang': 'en-US'}),
            os.path.join(PAGE_DIRECTORY,'posts',filename_without_ext,'index.html'),
            'webpage'
        )
    return {
        'title': title,
        'description': description,
        'link': f'{BASE_URL}/posts/{filename_without_ext}',
        'published': published,
        'pagename': filename_without_ext
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
            wrap('description', [item['description']]) if item['description'] else '',
            wrap('guid', [item['link']])
        ]) for item in items if item['published']
    ])
    return wrap('rss', [channel_tag], {
        'version': '2.0',
        'xmlns:atom': 'http://www.w3.org/2005/Atom'
    })

def generateIndex(items):
    return wrap('html',[
        headerElement(),
        bodyElement('', 'This is where I put my finest posts.', wrap('ul',[
            wrap('li',[
                wrap('a', [item['title']], {'href': item['pagename']}),
                (' - ' + item['description']) if item['description'] else ''
            ]) for item in items if item['published']
        ]))
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
for file in os.listdir('posts'):
    filename = os.fsdecode(file)
    if filename.endswith('.xml'):
        filepath = os.path.join(os.getcwd(),'posts',filename)
        items.append(generatePost(filename, filepath))
clean_and_write(
    generateRSS(items),
    os.path.join(PAGE_DIRECTORY,'rss.xml'),
    'rss'
)
clean_and_write(
    generateIndex(items),
    os.path.join(PAGE_DIRECTORY,'posts','index.html'),
    'webpage'
)
