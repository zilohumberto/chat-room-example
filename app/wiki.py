import wikipedia


def split_msg(msg):
    _search = msg.split("wiki:")
    if len(_search) > 1:
        return wikipedia.search(_search[1])
    return None
