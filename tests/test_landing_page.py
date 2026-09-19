"""Dependency-free checks for the root-level, offline-readable README guide.

Run from the repository root: python3 -m unittest discover -s tests -v
Browser interactions can be tested with any static server, or by opening index.html.
"""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)


class LandingPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PageParser()
        cls.page.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
        cls.ids = [attrs['id'] for _, attrs in cls.page.elements if 'id' in attrs]
        cls.text = ' '.join(cls.page.text)

    def test_unique_ids(self):
        self.assertEqual([], [id for id, count in Counter(self.ids).items() if count > 1])

    def test_local_links_and_assets_exist(self):
        for tag, attrs in self.page.elements:
            for key in ('href', 'src'):
                if key not in attrs:
                    continue
                url = urlsplit(attrs[key])
                if url.scheme or url.netloc:
                    continue
                with self.subTest(tag=tag, target=attrs[key]):
                    if url.path:
                        self.assertTrue((ROOT / unquote(url.path)).is_file())
                    elif url.fragment:
                        self.assertIn(unquote(url.fragment), self.ids)

    def test_chapters_cover_the_readme(self):
        chapters = {attrs['id'] for tag, attrs in self.page.elements if tag == 'section'}
        self.assertEqual(chapters, {
            'overview', 'how-it-works', 'get-started', 'supported-models',
            'performance', 'research', 'advanced-techniques', 'deepseek-v4',
            'reference', 'community',
        })
        for topic in ('Local cluster', 'second SSD', 'speculative', 'Repository layout',
                      'License', 'Engineering foundations', 'Open questions', 'Why “colibrì”'):
            with self.subTest(topic=topic):
                self.assertIn(topic.casefold(), self.text.casefold())

    def test_all_nine_model_families_are_documented(self):
        for model in ('GLM-5.2', 'GLM-5.3-Flash', 'Inkling', 'Kimi K3',
                      'DeepSeek V4 Flash', 'DeepSeek V4.1 Flash',
                      'Qwen3.8-Flash-Next', 'Qwen3.6', 'OLMoE'):
            self.assertIn(model, self.text)

    def test_no_remote_runtime_dependencies(self):
        for tag, attrs in self.page.elements:
            if tag == 'script':
                self.assertNotIn('src', attrs)
            if tag == 'link' and attrs.get('rel') == 'stylesheet':
                self.assertFalse(urlsplit(attrs['href']).netloc)
            if tag == 'img':
                self.assertFalse(urlsplit(attrs['src']).netloc)
                self.assertIn('alt', attrs)

    def test_accessible_controls_reference_existing_elements(self):
        self.assertEqual(1, sum(tag == 'h1' for tag, _ in self.page.elements))
        for tag, attrs in self.page.elements:
            for key in ('aria-controls', 'aria-labelledby'):
                for id in attrs.get(key, '').split():
                    with self.subTest(tag=tag, attribute=key, id=id):
                        self.assertIn(id, self.ids)
        self.assertTrue(any(tag == 'html' and attrs.get('lang') == 'en'
                            for tag, attrs in self.page.elements))


if __name__ == '__main__':
    unittest.main()
