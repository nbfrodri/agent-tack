"""Pagination, stale heads and read-only transport for PR review collection."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reviews', ROOT / 'skills/github-issues/assets/read-pr-reviews.py')
reviews = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reviews)


def page(nodes, cursor=None):
    return {'nodes': nodes, 'pageInfo': {'hasNextPage': cursor is not None, 'endCursor': cursor}}


class Reviews(unittest.TestCase):
    def test_pagination_deduplicates_and_rejects_stalled_cursor(self):
        self.assertEqual(reviews.connection_pages(page([{'id': 'one'}], 'next'),
                         lambda _: page([{'id': 'one'}, {'id': 'two'}])), [{'id': 'one'}, {'id': 'two'}])
        with self.assertRaises(ValueError):
            reviews.connection_pages(page([], 'same'), lambda _: page([], 'same'))

    def fixture(self, changed=False, partial=False):
        self.calls, self.reads = [], 0
        def client(*args):
            self.calls.append(args)
            if args[1] == 'graphql':
                if partial:
                    return {'errors': [{'message': 'unavailable'}]}
                if 'id=thread' in args:
                    return {'data': {'node': {'comments': page([{'id': 'second', 'body': 'still relevant'}])}}}
                thread = {'id': 'thread', 'isOutdated': True, 'isResolved': False,
                          'comments': page([{'id': 'first', 'body': 'review'}], 'more')}
                return {'data': {'repository': {'pullRequest': {'reviewThreads': page([thread])}}}}
            if args[1] == '--paginate':
                return [[{'id': 1}], [{'id': 2}]]
            self.reads += 1
            return {'head': {'sha': 'new' if changed and self.reads > 1 else 'head'}, 'base': {'sha': 'base'}}
        return client

    def test_collects_nested_comments_and_all_sources_without_writes(self):
        result = reviews.collect('owner/repo', 2, self.fixture())
        self.assertEqual(len(result['threads'][0]['comments']), 2)
        self.assertTrue(result['threads'][0]['isOutdated'])
        self.assertEqual(len(result['reviews']), 2)
        self.assertEqual(len(result['comments']), 2)
        self.assertFalse(any('mutation' in ' '.join(call) for call in self.calls))
        self.assertEqual(result, reviews.collect('owner/repo', 2, self.fixture()))

    def test_changed_head_and_partial_graphql_are_incomplete(self):
        for options in ({'changed': True}, {'partial': True}):
            with self.assertRaises(ValueError):
                reviews.collect('owner/repo', 2, self.fixture(**options))

    def test_invalid_repository_never_calls_github(self):
        with self.assertRaises(ValueError):
            reviews.collect('owner/repo; command', 1, lambda *args: self.fail('called GitHub'))


if __name__ == '__main__':
    unittest.main()
