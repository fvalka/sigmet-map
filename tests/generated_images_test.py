import unittest

from sigmet_map import FeatureProvider


class GeneratedImagesTest(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())


class FixtureFeatureProvider(FeatureProvider):
    def __init__(self, result):
        self._result = result

    def load(self, bbox):
        return self._result


if __name__ == '__main__':
    unittest.main()
