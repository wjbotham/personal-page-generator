from core.post import Post
import os
from operator import itemgetter
    
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

class Site:
    def __init__(self, config):
        self.config = {}
        self.config['source_directory'] = config['source_directory']
        self.config['static_site_directory'] = config['static_site_directory']
        self.config['base_url'] = config['base_url']
        
        with open(os.path.join(self.config['source_directory'], 'navigation-bar.html'), 'r') as file:
            self.nav_contents = file.read()
        
        posts = []
        tags = []
        for file in os.listdir(os.path.join(self.config['source_directory'],'posts')):
            filename = os.fsdecode(file)
            if filename.endswith('.xml'):
                filepath = os.path.join(self.config['source_directory'],'posts',filename)
                post = Post(filename, filepath)
                if post and post.published:
                    posts.append(post)
        self.posts = posts
        self.tags = sorted(set([tag for tag_list in map(lambda post: post.tags, posts) for tag in tag_list]))
    
    def rss(self):
        channel_tag = wrap('channel', [
            '<title>Wesley\'s Home Page</title>',
            f'<link>{self.config['base_url']}</link>',
            '<description>My personal page where I post things I don\'t want anyone to see.</description>',
            '<language>en-US</language>',
            '<docs>https://www.rssboard.org/rss-specification</docs>',
            wrap('atom:link', [], {
                'href': f'{self.config['base_url']}/rss.xml',
                'rel': 'self',
                'type': 'application/rss+xml'
            })
        ] + [
            wrap('item',[
                wrap('title', post.title),
                wrap('link', f'{self.config['base_url']}/posts/{post.pagename}'),
                wrap('description', post.description),
                wrap('guid', f'{self.config['base_url']}/posts/{post.pagename}')
            ]) for post in self.posts if post.published
        ])
        return wrap('rss', [channel_tag], {
            'version': '2.0',
            'xmlns:atom': 'http://www.w3.org/2005/Atom'
        })

    def primaryIndex(self):
        return wrap('html',[
            headerElement(),
            self.bodyElement('',
                wrap('p','')+
                wrap('center',[wrap('a', tag, {'href': f'../tags/{tag}'}) for tag in self.tags])+
                wrap('ul',[
                    wrap('li',[
                        wrap('a', post.title, {'href': post.pagename}),
                        (' - ' + post.description),
                        ' ',
                        wrap('span', [
                            'published ',
                            post.created_at.strftime('%b %d %Y'),
                            ', updated '+post.updated_at.strftime('%b %d %Y') if post.created_at != post.updated_at else ''
                        ], {'class': 'post_metadata'})
                    ]) for post in sorted(self.posts,key=lambda post: post.created_at,reverse=True) if post.published
                ])
            )
        ], {'lang': 'en-US'})
    
    def tagIndexes(self):
        return { selected_tag: self.tagIndex(selected_tag) for selected_tag in self.tags }
    
    def tagIndex(self, selected_tag):
        return wrap('html',[
            headerElement(),
            self.bodyElement('',
                wrap('p','')+
                wrap('center',[
                    (wrap('b',tag) if tag == selected_tag else wrap('a', tag, {'href': f'../{tag}'})) for tag in self.tags
                ])+
                wrap('ul',[
                    wrap('li',[
                        wrap('a', post.title, {'href': f'../posts/{post.pagename}'}),
                        (' - ' + post.description),
                        ' ',
                        wrap('span', [
                            'published ',
                            post.created_at.strftime('%b %d %Y'),
                            ', updated '+post.updated_at.strftime('%b %d %Y') if post.created_at != post.updated_at else ''
                        ], {'class': 'post_metadata'})
                    ]) for post in sorted(self.posts,key=lambda post: post.created_at,reverse=True) if post.published and selected_tag in post.tags
                ])
            )
        ], {'lang': 'en-US'})

    def bodyElement(self, title: str, content: str, created_at = None, updated_at = None):
        return wrap('body', [
            '<nav>',
            self.nav_contents,
            '</nav>',
            mainElement(title, content, created_at, updated_at)
        ])