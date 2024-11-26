def wrap(tag, contents, attributes=None):
    attribute_string = "".join(f' {key}="{attributes[key]}"' for key in attributes) if attributes else ""
    return "".join(
        [
            "<%s%s>" % (tag, attribute_string),
            "".join(filter(lambda x: x is not None, contents)),
            "</%s>" % tag,
        ]
    )
