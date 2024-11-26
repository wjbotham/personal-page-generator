# run resulting page locally with:
#   cd .\Projects\personal-page\
#   python -m http.server 8000

from core.site import Site
import os
import io
from xml.etree import ElementTree
import shutil

PAGE_DIRECTORY = os.path.join(os.path.dirname(os.getcwd()),'personal-page')

def clean_and_write(xml_string: str, path: str, kind: str):
    assert(kind == 'rss' or kind == 'webpage')
    tree = ElementTree.parse(io.StringIO(xml_string))
    ElementTree.indent(tree.getroot())
    if kind == 'rss':
        ElementTree.register_namespace('atom','http://www.w3.org/2005/Atom')
        tree.write(path, method='xml')
    elif kind == 'webpage':
        tree.write(path, method='html')
        
site = Site({
    'base_url': 'https://wajib.space',
    'post_xml_directory': 'posts',
    'static_site_directory': os.path.join(os.path.dirname(os.getcwd()),'personal-page')
})
clean_and_write(
    site.rss(),
    os.path.join(PAGE_DIRECTORY,'rss.xml'),
    'rss'
)
clean_and_write(
    site.primaryIndex(),
    os.path.join(PAGE_DIRECTORY,'posts','index.html'),
    'webpage'
)
for tag_name,tag_index in site.tagIndexes().items():
    tag_directory = os.path.join(PAGE_DIRECTORY,'tags',tag_name)
    if not os.path.isdir(tag_directory):
        os.mkdir(tag_directory)
    clean_and_write(
        tag_index,
        os.path.join(tag_directory,'index.html'),
        'webpage'
    )
shutil.copy(
    os.path.join(os.getcwd(), 'default.css'),
    os.path.join(PAGE_DIRECTORY, 'default.css')
)
