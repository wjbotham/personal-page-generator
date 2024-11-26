from xml.etree import ElementTree
from datetime import date
from modules.helpers import wrap
import re


class Post:
    def __init__(self, filename, filepath):
        try:
            source = ElementTree.parse(filepath)
        except ElementTree.ParseError as err:
            print(f"parse error in {filename}: {err}")
            return None
        published = False
        for child in source.getroot():
            if child.tag == "title":
                title = child.text
            elif child.tag == "description":
                description = child.text
            elif child.tag == "html_content":
                content = ""
                for subchild in child:
                    content += ElementTree.tostring(subchild, encoding="unicode")
            elif child.tag == "published":
                if child.text == "true":
                    published = True
            elif child.tag == "created_at":
                year, month, day = map(int, child.text.split("-"))
                created_at = date(year, month, day)
            elif child.tag == "updated_at":
                year, month, day = map(int, child.text.split("-"))
                updated_at = date(year, month, day)
            elif child.tag == "tags":
                tag_names = []
                for subchild in child:
                    if subchild.tag == "tag":
                        tag_names += [subchild.text]
        self.title = title
        self.description = description
        self.published = published
        self.pagename = re.sub(r"\.xml$", "", filename)
        self.created_at = created_at
        self.updated_at = updated_at
        self.tags = tag_names

    def rss_item(self, link_root):
        return wrap(
            "item",
            [
                wrap("title", self.title),
                wrap("link", f"{link_root}/{self.pagename}"),
                wrap("description", self.description),
                wrap("guid", f"{link_root}/{self.pagename}"),
            ],
        )
