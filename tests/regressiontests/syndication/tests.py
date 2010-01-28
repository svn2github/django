import datetime
from django.contrib.syndication import feeds, views
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.utils import tzinfo
from models import Entry
from xml.dom import minidom

try:
    set
except NameError:
    from sets import Set as set

class FeedTestCase(TestCase):
    fixtures = ['feeddata.json']

    def assertChildNodes(self, elem, expected):
        actual = set([n.nodeName for n in elem.childNodes])
        expected = set(expected)
        self.assertEqual(actual, expected)

    def assertChildNodeContent(self, elem, expected):
        for k, v in expected.items():
            self.assertEqual(
                elem.getElementsByTagName(k)[0].firstChild.wholeText, v)

    def assertCategories(self, elem, expected):
        self.assertEqual(set(i.firstChild.wholeText for i in elem.childNodes if i.nodeName == 'category'), set(expected));

######################################
# Feed view
######################################

class SyndicationFeedTest(FeedTestCase):
    """
    Tests for the high-level syndication feed framework.
    """

    def test_rss2_feed(self):
        """
        Test the structure and content of feeds generated by Rss201rev2Feed.
        """
        response = self.client.get('/syndication/rss2/')
        doc = minidom.parseString(response.content)

        # Making sure there's only 1 `rss` element and that the correct
        # RSS version was specified.
        feed_elem = doc.getElementsByTagName('rss')
        self.assertEqual(len(feed_elem), 1)
        feed = feed_elem[0]
        self.assertEqual(feed.getAttribute('version'), '2.0')

        # Making sure there's only one `channel` element w/in the
        # `rss` element.
        chan_elem = feed.getElementsByTagName('channel')
        self.assertEqual(len(chan_elem), 1)
        chan = chan_elem[0]
        self.assertChildNodes(chan, ['title', 'link', 'description', 'language', 'lastBuildDate', 'item', 'atom:link', 'ttl', 'copyright', 'category'])
        self.assertChildNodeContent(chan, {
            'title': 'My blog',
            'description': 'A more thorough description of my blog.',
            'link': 'http://example.com/blog/',
            'language': 'en',
            'lastBuildDate': 'Thu, 03 Jan 2008 13:30:00 -0600',
            #'atom:link': '',
            'ttl': '600',
            'copyright': 'Copyright (c) 2007, Sally Smith',
        })
        self.assertCategories(chan, ['python', 'django']);

        # Ensure the content of the channel is correct
        self.assertChildNodeContent(chan, {
            'title': 'My blog',
            'link': 'http://example.com/blog/',
        })

        # Check feed_url is passed
        self.assertEqual(
            chan.getElementsByTagName('atom:link')[0].getAttribute('href'),
            'http://example.com/syndication/rss2/'
        )

        items = chan.getElementsByTagName('item')
        self.assertEqual(len(items), Entry.objects.count())
        self.assertChildNodeContent(items[0], {
            'title': 'My first entry',
            'description': 'Overridden description: My first entry',
            'link': 'http://example.com/blog/1/',
            'guid': 'http://example.com/blog/1/',
            'pubDate': 'Tue, 01 Jan 2008 12:30:00 -0600',
            'author': 'test@example.com (Sally Smith)',
        })
        self.assertCategories(items[0], ['python', 'testing']);

        for item in items:
            self.assertChildNodes(item, ['title', 'link', 'description', 'guid', 'category', 'pubDate', 'author'])

    def test_rss091_feed(self):
        """
        Test the structure and content of feeds generated by RssUserland091Feed.
        """
        response = self.client.get('/syndication/rss091/')
        doc = minidom.parseString(response.content)

        # Making sure there's only 1 `rss` element and that the correct
        # RSS version was specified.
        feed_elem = doc.getElementsByTagName('rss')
        self.assertEqual(len(feed_elem), 1)
        feed = feed_elem[0]
        self.assertEqual(feed.getAttribute('version'), '0.91')

        # Making sure there's only one `channel` element w/in the
        # `rss` element.
        chan_elem = feed.getElementsByTagName('channel')
        self.assertEqual(len(chan_elem), 1)
        chan = chan_elem[0]
        self.assertChildNodes(chan, ['title', 'link', 'description', 'language', 'lastBuildDate', 'item', 'atom:link', 'ttl', 'copyright', 'category'])

        # Ensure the content of the channel is correct
        self.assertChildNodeContent(chan, {
            'title': 'My blog',
            'link': 'http://example.com/blog/',
        })
        self.assertCategories(chan, ['python', 'django'])

        # Check feed_url is passed
        self.assertEqual(
            chan.getElementsByTagName('atom:link')[0].getAttribute('href'),
            'http://example.com/syndication/rss091/'
        )

        items = chan.getElementsByTagName('item')
        self.assertEqual(len(items), Entry.objects.count())
        self.assertChildNodeContent(items[0], {
            'title': 'My first entry',
            'description': 'Overridden description: My first entry',
            'link': 'http://example.com/blog/1/',
        })
        for item in items:
            self.assertChildNodes(item, ['title', 'link', 'description'])
            self.assertCategories(item, [])

    def test_atom_feed(self):
        """
        Test the structure and content of feeds generated by Atom1Feed.
        """
        response = self.client.get('/syndication/atom/')
        feed = minidom.parseString(response.content).firstChild

        self.assertEqual(feed.nodeName, 'feed')
        self.assertEqual(feed.getAttribute('xmlns'), 'http://www.w3.org/2005/Atom')
        self.assertChildNodes(feed, ['title', 'subtitle', 'link', 'id', 'updated', 'entry', 'rights', 'category', 'author'])
        for link in feed.getElementsByTagName('link'):
            if link.getAttribute('rel') == 'self':
                self.assertEqual(link.getAttribute('href'), 'http://example.com/syndication/atom/')

        entries = feed.getElementsByTagName('entry')
        self.assertEqual(len(entries), Entry.objects.count())
        for entry in entries:
            self.assertChildNodes(entry, ['title', 'link', 'id', 'summary', 'category', 'updated', 'rights', 'author'])
            summary = entry.getElementsByTagName('summary')[0]
            self.assertEqual(summary.getAttribute('type'), 'html')

    def test_custom_feed_generator(self):
        response = self.client.get('/syndication/custom/')
        feed = minidom.parseString(response.content).firstChild

        self.assertEqual(feed.nodeName, 'feed')
        self.assertEqual(feed.getAttribute('django'), 'rocks')
        self.assertChildNodes(feed, ['title', 'subtitle', 'link', 'id', 'updated', 'entry', 'spam', 'rights', 'category', 'author'])

        entries = feed.getElementsByTagName('entry')
        self.assertEqual(len(entries), Entry.objects.count())
        for entry in entries:
            self.assertEqual(entry.getAttribute('bacon'), 'yum')
            self.assertChildNodes(entry, ['title', 'link', 'id', 'summary', 'ministry', 'rights', 'author', 'updated', 'category'])
            summary = entry.getElementsByTagName('summary')[0]
            self.assertEqual(summary.getAttribute('type'), 'html')

    def test_title_escaping(self):
        """
        Tests that titles are escaped correctly in RSS feeds.
        """
        response = self.client.get('/syndication/rss2/')
        doc = minidom.parseString(response.content)
        for item in doc.getElementsByTagName('item'):
            link = item.getElementsByTagName('link')[0]
            if link.firstChild.wholeText == 'http://example.com/blog/4/':
                title = item.getElementsByTagName('title')[0]
                self.assertEquals(title.firstChild.wholeText, u'A &amp; B &lt; C &gt; D')

    def test_naive_datetime_conversion(self):
        """
        Test that datetimes are correctly converted to the local time zone.
        """
        # Naive date times passed in get converted to the local time zone, so
        # check the recived zone offset against the local offset.
        response = self.client.get('/syndication/naive-dates/')
        doc = minidom.parseString(response.content)
        updated = doc.getElementsByTagName('updated')[0].firstChild.wholeText
        tz = tzinfo.LocalTimezone(datetime.datetime.now())
        now = datetime.datetime.now(tz)
        self.assertEqual(updated[-6:], str(now)[-6:])

    def test_aware_datetime_conversion(self):
        """
        Test that datetimes with timezones don't get trodden on.
        """
        response = self.client.get('/syndication/aware-dates/')
        doc = minidom.parseString(response.content)
        updated = doc.getElementsByTagName('updated')[0].firstChild.wholeText
        self.assertEqual(updated[-6:], '+00:42')

    def test_feed_url(self):
        """
        Test that the feed_url can be overridden.
        """
        response = self.client.get('/syndication/feedurl/')
        doc = minidom.parseString(response.content)
        for link in doc.getElementsByTagName('link'):
            if link.getAttribute('rel') == 'self':
                self.assertEqual(link.getAttribute('href'), 'http://example.com/customfeedurl/')

    def test_item_link_error(self):
        """
        Test that a ImproperlyConfigured is raised if no link could be found
        for the item(s).
        """
        self.assertRaises(ImproperlyConfigured,
                          self.client.get,
                          '/syndication/articles/')

    def test_template_feed(self):
        """
        Test that the item title and description can be overridden with
        templates.
        """
        response = self.client.get('/syndication/template/')
        doc = minidom.parseString(response.content)
        feed = doc.getElementsByTagName('rss')[0]
        chan = feed.getElementsByTagName('channel')[0]
        items = chan.getElementsByTagName('item')

        self.assertChildNodeContent(items[0], {
            'title': 'Title in your templates: My first entry',
            'description': 'Description in your templates: My first entry',
            'link': 'http://example.com/blog/1/',
        })

    def test_add_domain(self):
        """
        Test add_domain() prefixes domains onto the correct URLs.
        """
        self.assertEqual(
            views.add_domain('example.com', '/foo/?arg=value'),
            'http://example.com/foo/?arg=value'
        )
        self.assertEqual(
            views.add_domain('example.com', 'http://djangoproject.com/doc/'),
            'http://djangoproject.com/doc/'
        )
        self.assertEqual(
            views.add_domain('example.com', 'https://djangoproject.com/doc/'),
            'https://djangoproject.com/doc/'
        )
        self.assertEqual(
            views.add_domain('example.com', 'mailto:uhoh@djangoproject.com'),
            'mailto:uhoh@djangoproject.com'
        )


######################################
# Deprecated feeds
######################################

class DeprecatedSyndicationFeedTest(FeedTestCase):
    """
    Tests for the deprecated API (feed() view and the feed_dict etc).
    """

    def test_empty_feed_dict(self):
        """
        Test that an empty feed_dict raises a 404.
        """
        response = self.client.get('/syndication/depr-feeds-empty/aware-dates/')
        self.assertEquals(response.status_code, 404)

    def test_nonexistent_slug(self):
        """
        Test that a non-existent slug raises a 404.
        """
        response = self.client.get('/syndication/depr-feeds/foobar/')
        self.assertEquals(response.status_code, 404)

    def test_rss_feed(self):
        """
        A simple test for Rss201rev2Feed feeds generated by the deprecated
        system.
        """
        response = self.client.get('/syndication/depr-feeds/rss/')
        doc = minidom.parseString(response.content)
        feed = doc.getElementsByTagName('rss')[0]
        self.assertEqual(feed.getAttribute('version'), '2.0')

        chan = feed.getElementsByTagName('channel')[0]
        self.assertChildNodes(chan, ['title', 'link', 'description', 'language', 'lastBuildDate', 'item', 'atom:link'])

        items = chan.getElementsByTagName('item')
        self.assertEqual(len(items), Entry.objects.count())

    def test_complex_base_url(self):
        """
        Tests that the base url for a complex feed doesn't raise a 500
        exception.
        """
        response = self.client.get('/syndication/depr-feeds/complex/')
        self.assertEquals(response.status_code, 404)

