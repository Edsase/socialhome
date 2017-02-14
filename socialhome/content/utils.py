import re

import bleach
from bs4 import BeautifulSoup


ILLEGAL_TAG_CHARS = "!#$%^&*+.,@£/()=?`'\\{[]}~;:\""


def safe_text_for_markdown(text):
    """Clean the text using bleach but keep certain Markdown sections.

    Markdown code ie ` or ``` combos. For single `, do not allow line breaks between the tag.
    Quotes ie '> ' which bleach would clean up.
    """
    # Regexp match all ` and ``` pairs
    codes = re.findall(r"`(?!`)[^\r\n].*[^\r\n]`(?!`)", text, flags=re.DOTALL) + \
            re.findall(r"```.*```", text, flags=re.DOTALL)
    # Store to safety, replacing with markers
    safety = []
    for counter, code in enumerate(codes, 1):
        safety.append(code)
        text = text.replace(code, "%%safe_text_for_markdown codes in safety %s%%" % counter, 1)
    # Store quotes next
    text = re.sub(r"(^> )", "%%safe_quote_in_start%%", text)
    text = re.sub(r"(\n> )", "%%safe_quote_in_new_line%%", text, flags=re.DOTALL)
    # Nuke all html, scripts, etc
    text = bleach.clean(text)
    # Return quotes
    text = text.replace("%%safe_quote_in_start%%", "> ")
    text = text.replace("%%safe_quote_in_new_line%%", "\n> ")
    # Return ` and ``` pairs from safety
    for counter, code in enumerate(safety, 1):
        text = text.replace("%%safe_text_for_markdown codes in safety %s%%" % counter, code, 1)
    return text


def safe_text(text):
    """Clean text, stripping all tags, attributes and styles."""
    return bleach.clean(text, tags=[], attributes=[], styles=[], strip=True)


def make_nsfw_safe(text):
    """Make NSFW safer by adding click-to-show class to images."""
    soup = BeautifulSoup(text, "lxml")
    images = soup.find_all("img")

    for image in images:
        if image.get("class"):
            image["class"] = "%s nsfw" % " ".join(image.get("class"))
        else:
            image["class"] = "nsfw"
        image.replace_with(image)

    result = str(soup)
    # We don't want html/body, which BeautifulSoup kindly wraps our new HTML in
    if result.startswith("<html><body>") and result.endswith("</body></html>"):
        result = result[len("<html><body>"):-len("</body></html>")]
    return result


def find_urls_in_text(text):
    """Find url's from text.

    URL matching by design only picks up "orphan" urls which are not href attributes or markdown links.
    There must be an empty space, line feed or text start before the url for a match to happen.

    Note, this is not entirely accurate, we're just trying to match as many as we can, allowing possibly
    a few false positives.
    """
    urls = re.findall(r'^https?://[\w\./\?=#\-&_%\+~:\[\]@\!\$\(\)\*,;]*', text) + \
           re.findall(r'(?<=[ \n]{1})https?://[\w\./\?=#\-&_%\+~:\[\]@\!\$\(\)\*,;]*', text)
    return urls


def test_and_clean_tag(tag):
    """Test and clean a given tag

    A tag is invalid if it contains illegal characters, except if the illegal
    character is at the end, in which case we just strip it. This allows for tags
    ending in special characters like question marks still to be recognized.
    """
    if not tag:
        return tag
    majority, ending = tag[0:len(tag)-1], tag[-1]
    for char in ILLEGAL_TAG_CHARS:
        if char in majority:
            return False
    if ending in ILLEGAL_TAG_CHARS:
        return majority
    return tag


def find_tags_in_text(text):
    """Given a block of text, identify and clean tags out of it.

    All tags are converted to lowercase and returned in a set to
    ensure no duplicates are returned.

    :rtype: set
    """
    # TODO: skip code blocks
    # TODO: identify also tags prefixed with ( or [
    tags = {word.strip("#").lower() for word in text.split() if word.startswith("#") and len(word) > 1}
    fixed_tags = set()
    for tag in tags:
        test_result = test_and_clean_tag(tag)
        if test_result:
            fixed_tags.add(test_result)
    return fixed_tags
