from core.post import Post
import os
import io
from xml.etree import ElementTree
import shutil


def clean_and_write(xml_string: str, path: str, kind: str):
    assert kind == "rss" or kind == "webpage"
    tree = ElementTree.parse(io.StringIO(xml_string))
    ElementTree.indent(tree.getroot())
    if kind == "rss":
        ElementTree.register_namespace("atom", "http://www.w3.org/2005/Atom")
        tree.write(path, method="xml")
    elif kind == "webpage":
        tree.write(path, method="html")


def wrap(tag, contents, attributes=None):
    attribute_string = "".join(f' {key}="{attributes[key]}"' for key in attributes) if attributes else ""
    return "".join(
        [
            "<%s%s>" % (tag, attribute_string),
            "".join(filter(lambda x: x is not None, contents)),
            "</%s>" % tag,
        ]
    )


def headerElement(title=None):
    return wrap(
        "head",
        [
            '<meta name="viewport" content="width=device-width, initial-scale=1.0"/>',
            '<script src="https://code.jquery.com/jquery-3.6.1.js"></script>',
            '<link rel="stylesheet" href="/default.css"/>',
            '<link rel="alternate" type="application/rss+xml" href="/rss.xml" title="RSS Feed"/>',
            f'<title>Wesley\'s Home Page{" - "+title if title else ""}</title>',
        ],
    )


def mainElement(title: str, content: str, created_at=None, updated_at=None):
    return wrap(
        "main",
        [
            ("<h2>%s</h2>" % title) if title else "",
            content,
            wrap(
                "span",
                ["published ", created_at.strftime("%b %d %Y")],
                {"class": "post_metadata"},
            )
            if created_at
            else "",
            "<br/>"
            + wrap(
                "span",
                [
                    "updated ",
                    updated_at.strftime("%b %d %Y"),
                ],
                {"class": "post_metadata"},
            )
            if (updated_at and created_at != updated_at)
            else "",
        ],
    )


class Site:
    def __init__(self, config):
        self.source_directory = config["source_directory"]
        self.static_site_directory = config["static_site_directory"]
        self.base_url = config["base_url"]

        with open(os.path.join(self.source_directory, "navigation-bar.html"), "r") as file:
            self.nav_contents = file.read()

        self.posts = []
        for file in os.listdir(os.path.join(self.source_directory, "posts")):
            filename = os.fsdecode(file)
            if filename.endswith(".xml"):
                filepath = os.path.join(self.source_directory, "posts", filename)
                post = Post(filename, filepath)
                if post and post.published:
                    self.posts.append(post)

        self.tags = sorted(set([tag for tag_list in map(lambda post: post.tags, self.posts) for tag in tag_list]))

    def rss(self):
        channel_tag = wrap(
            "channel",
            [
                "<title>Wesley's Home Page</title>",
                f"<link>{self.base_url}</link>",
                "<description>My personal page where I post things I don't want anyone to see.</description>",
                "<language>en-US</language>",
                "<docs>https://www.rssboard.org/rss-specification</docs>",
                wrap(
                    "atom:link",
                    [],
                    {
                        "href": f"{self.base_url}/rss.xml",
                        "rel": "self",
                        "type": "application/rss+xml",
                    },
                ),
            ]
            + [
                wrap(
                    "item",
                    [
                        wrap("title", post.title),
                        wrap("link", f"{self.base_url}/posts/{post.pagename}"),
                        wrap("description", post.description),
                        wrap("guid", f"{self.base_url}/posts/{post.pagename}"),
                    ],
                )
                for post in self.posts
                if post.published
            ],
        )
        return wrap(
            "rss",
            [channel_tag],
            {"version": "2.0", "xmlns:atom": "http://www.w3.org/2005/Atom"},
        )

    def tagIndexes(self):
        return {selected_tag: self.index(selected_tag) for selected_tag in self.tags}

    def index(self, selected_tag=None):
        return wrap(
            "html",
            [
                headerElement(selected_tag or "Posts"),
                self.bodyElement(
                    "",
                    wrap("p", "")
                    + wrap(
                        "center",
                        [(wrap("b", tag) if tag == selected_tag else wrap("a", tag, {"href": f"/tags/{tag}"})) for tag in self.tags],
                    )
                    + wrap(
                        "ul",
                        [
                            wrap(
                                "li",
                                [
                                    wrap(
                                        "a",
                                        post.title,
                                        {"href": f"/posts/{post.pagename}"},
                                    ),
                                    (" - " + post.description),
                                    " ",
                                    wrap(
                                        "span",
                                        [
                                            "published ",
                                            post.created_at.strftime("%b %d %Y"),
                                            ", updated " + post.updated_at.strftime("%b %d %Y") if post.created_at != post.updated_at else "",
                                        ],
                                        {"class": "post_metadata"},
                                    ),
                                ],
                            )
                            for post in sorted(
                                self.posts,
                                key=lambda post: post.created_at,
                                reverse=True,
                            )
                            if post.published and (selected_tag in post.tags or not selected_tag)
                        ],
                    ),
                ),
            ],
            {"lang": "en-US"},
        )

    def bodyElement(self, title: str, content: str, created_at=None, updated_at=None):
        return wrap(
            "body",
            [
                "<nav>",
                self.nav_contents,
                "</nav>",
                mainElement(title, content, created_at, updated_at),
            ],
        )

    def generate_static_files(self):
        clean_and_write(
            self.rss(),
            os.path.join(self.static_site_directory, "rss.xml"),
            "rss",
        )
        clean_and_write(
            self.index(),
            os.path.join(self.static_site_directory, "posts", "index.html"),
            "webpage",
        )
        for tag_name, tag_index in self.tagIndexes().items():
            tag_directory = os.path.join(self.static_site_directory, "tags", tag_name)
            if not os.path.isdir(tag_directory):
                os.mkdir(tag_directory)
            clean_and_write(tag_index, os.path.join(tag_directory, "index.html"), "webpage")
        shutil.copy(
            os.path.join(self.source_directory, "default.css"),
            os.path.join(self.static_site_directory, "default.css"),
        )
