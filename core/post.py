from xml.etree import ElementTree
from datetime import date
from modules.helpers import wrap,write
import re


class Post:
    def __init__(self, filename, filepath):
        try:
            source = ElementTree.parse(filepath)
        except ElementTree.ParseError as err:
            print(f"parse error in {filename}: {err}")
            return None
        self.pagename = re.sub(r"\.xml$", "", filename)
        self.published = False
        self.description = ""
        self.content = ""
        for child in source.getroot():
            if child.tag == "title":
                self.title = child.text
            elif child.tag == "description":
                self.description = child.text
            elif child.tag == "html_content":
                for subchild in child:
                    self.content += ElementTree.tostring(subchild, encoding="unicode")
            elif child.tag == "published":
                if child.text == "true":
                    self.published = True
            elif child.tag == "created_at":
                year, month, day = map(int, child.text.split("-"))
                self.created_at = date(year, month, day)
            elif child.tag == "updated_at":
                year, month, day = map(int, child.text.split("-"))
                self.updated_at = date(year, month, day)
            elif child.tag == "tags":
                self.tags = []
                for subchild in child:
                    if subchild.tag == "tag":
                        self.tags += [subchild.text]

    def rss_item(self, link_root):
        return wrap(
            "item",
            [
                wrap("title", self.title),
                wrap("link", f"{link_root}/posts/{self.pagename}"),
                wrap("description", self.description),
                wrap("guid", f"{link_root}/posts/{self.pagename}"),
            ],
        )

    def list_item(self):
        return wrap(
            "li",
            [
                wrap("a", self.title, {"href": f"/posts/{self.pagename}"}),
                f" - {self.description} " if self.description else "",
                wrap(
                    "span",
                    [
                        "published ",
                        self.created_at.strftime("%b %d %Y"),
                        ", updated " + self.updated_at.strftime("%b %d %Y") if self.created_at != self.updated_at else "",
                    ],
                    {"class": "post_metadata"},
                ),
            ],
        )
