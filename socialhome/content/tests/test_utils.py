from django.test import TestCase

from socialhome.content.utils import safe_text_for_markdown, safe_text, make_nsfw_safe, find_urls_in_text, \
    find_tags_in_text

PLAIN_TEXT = "abcdefg kissa kävelee"
MARKDOWN_TEXT = "## header\n\nFoo Bar. *fooo*"
MARKDOWN_QUOTES_TEXT = "> foo\n> bar > foo"
SCRIPT_TEXT = "<script>console.log</script>"
MARKDOWN_CODE_TEXT = "`\n<script>alert('yup');</script>\n`\n\n`<script>alert('yup');</script>`\n\n```\n" \
                     "<script>alert('yap');</script>\n```"
HTML_TEXT = "<a href='foo'>bar</a><b>cee</b><em>daaa<div>faa</div>"


class TestSafeTextForMarkdown(object):
    def test_plain_text_survives(self):
        assert safe_text_for_markdown(PLAIN_TEXT) == PLAIN_TEXT

    def test_text_with_markdown_survives(self):
        assert safe_text_for_markdown(MARKDOWN_TEXT) == MARKDOWN_TEXT

    def test_text_with_markdown_code_survives(self):
        assert safe_text_for_markdown(MARKDOWN_CODE_TEXT) == \
               "`\n&lt;script&gt;alert('yup');&lt;/script&gt;\n`\n\n`<script>alert('yup');</script>`\n\n```\n" \
               "<script>alert('yap');</script>\n```"

    def test_text_with_script_is_cleaned(self):
        assert safe_text_for_markdown(SCRIPT_TEXT) == "&lt;script&gt;console.log&lt;/script&gt;"

    def test_text_with_html_is_cleaned(self):
        assert safe_text_for_markdown(HTML_TEXT) == '<a href="foo">bar</a><b>cee</b><em>daaa&lt;div&gt;faa&lt' \
                                                         ';/div&gt;</em>'

    def test_text_with_quotes_survives(self):
        assert safe_text_for_markdown(MARKDOWN_QUOTES_TEXT) == "> foo\n> bar &gt; foo"


class TestSafeText(object):
    def test_plain_text_survives(self):
        assert safe_text(PLAIN_TEXT) == PLAIN_TEXT

    def test_text_with_markdown_survives(self):
        assert safe_text(MARKDOWN_TEXT) == MARKDOWN_TEXT

    def test_text_with_markdown_code_is_cleaned(self):
        assert safe_text(MARKDOWN_CODE_TEXT) == "`\nalert('yup');\n`\n\n`alert('yup');`\n\n```\n" \
                                                "alert('yap');\n```"

    def test_text_with_script_is_cleaned(self):
        assert safe_text(SCRIPT_TEXT) == "console.log"

    def test_text_with_html_is_cleaned(self):
        assert safe_text(HTML_TEXT) == "barceedaaafaa"


class TestMakeNSFWSafe(TestCase):
    def setUp(self):
        super(TestMakeNSFWSafe, self).setUp()
        self.nsfw_text = '<div>FooBar</div><div><img src="localhost"/></div><div>#nsfw</div>'
        self.nsfw_text_with_classes = '<div>FooBar</div><div><img class="foobar" src="localhost"/></div>' \
                                      '<div>#nsfw</div>'
        self.nsfw_text_empty_class = '<div>FooBar</div><div><img class="" src="localhost"/></div>' \
                                     '<div>#nsfw</div>'
        self.nsfw_text_many_classes = '<div>FooBar</div><div><img class="foo bar" src="localhost"/></div>' \
                                      '<div>#nsfw</div>'

    def test_adds_nsfw_class(self):
        self.assertEqual(
            make_nsfw_safe(self.nsfw_text),
            '<div>FooBar</div><div><img class="nsfw" src="localhost"/></div><div>#nsfw</div>'
        )
        self.assertEqual(
            make_nsfw_safe(self.nsfw_text_with_classes),
            '<div>FooBar</div><div><img class="foobar nsfw" src="localhost"/></div><div>#nsfw</div>'
        )
        self.assertEqual(
            make_nsfw_safe(self.nsfw_text_empty_class),
            '<div>FooBar</div><div><img class=" nsfw" src="localhost"/></div><div>#nsfw</div>'
        )
        self.assertEqual(
            make_nsfw_safe(self.nsfw_text_many_classes),
            '<div>FooBar</div><div><img class="foo bar nsfw" src="localhost"/></div><div>#nsfw</div>'
        )


class TestFindUrlsInText(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestFindUrlsInText, cls).setUpTestData()
        cls.starts_with_url = "https://example.com/foobar"
        cls.http_starts_with_url = "http://example.com/foobar"
        cls.numbers = "http://foo123.633.com"
        cls.special_chars = "https://example.com/~:[]@!$()*,;_%20+wat.wot?foo=bar&bar=foo#rokkenroll"
        cls.urls_in_text = "fewfe https://example1.com grheiugheriu\nhttps://example2.com " \
                           "fhuiwehfui https://example-3.com\nfwfefewjuio"
        cls.href_and_markdown = "foo <a href='https://example.com'>bar</a> " \
                                "<a href=\"https://example.com\">bar</a>" \
                                "[waat](https://example.com)"

    def test_starts_with_url(self):
        urls = find_urls_in_text(self.starts_with_url)
        self.assertEqual(urls, [self.starts_with_url])
        urls = find_urls_in_text(self.http_starts_with_url)
        self.assertEqual(urls, [self.http_starts_with_url])

    def test_numbers(self):
        urls = find_urls_in_text(self.numbers)
        self.assertEqual(urls, [self.numbers])

    def test_special_chars(self):
        urls = find_urls_in_text(self.special_chars)
        self.assertEqual(urls, [self.special_chars])

    def test_urls_in_text(self):
        urls = find_urls_in_text(self.urls_in_text)
        self.assertEqual(urls, [
            "https://example1.com", "https://example2.com", "https://example-3.com"
        ])

    def test_href_markdown_etc_skipped(self):
        urls = find_urls_in_text(self.href_and_markdown)
        self.assertEqual(urls, [])


class TestFindTagsInText(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.text = "#starting and #MixED with some #line\nendings also tags can\n#start on new line"
        cls.invalid = "#a!a #a#a #a$a #a%a #a^a #a&a #a*a #a+a #a.a #a,a #a@a #a£a #a/a #a(a #a)a #a=a #a?a #a`a " \
                      "#a'a #a\\a #a{a #a[a #a]a #a}a #a~a #a;a #a:a #a\"a"
        cls.endings = "#parenthesis) #exp! #list]"

    def test_all_tags_are_parsed_from_text(self):
        tags = find_tags_in_text(self.text)
        self.assertEqual(
            tags,
            {"starting", "mixed", "line", "start"}
        )

    def test_invalid_text_returns_no_tags(self):
        self.assertEqual(find_tags_in_text(self.invalid), set())

    def test_endings_are_filtered_out(self):
        tags = find_tags_in_text(self.endings)
        self.assertEqual(
            tags,
            {"parenthesis", "exp", "list"}
        )
