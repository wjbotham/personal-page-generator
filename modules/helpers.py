from xml.etree import ElementTree
import io

def wrap(tag, contents, attributes=None):
    attribute_string = "".join(f' {key}="{attributes[key]}"' for key in attributes) if attributes else ""
    return "".join(
        [
            "<%s%s>" % (tag, attribute_string),
            "".join(filter(lambda x: x is not None, contents)),
            "</%s>" % tag,
        ]
    )

def write(xml_string: str, path: str, kind: str):
    assert kind == "rss" or kind == "webpage"
    tree = ElementTree.parse(io.StringIO(xml_string))
    ElementTree.indent(tree.getroot())
    if kind == "rss":
        ElementTree.register_namespace("atom", "http://www.w3.org/2005/Atom")
        tree.write(path, method="xml")
    elif kind == "webpage":
        tree.write(path, method="html")
