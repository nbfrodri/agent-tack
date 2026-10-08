#!/usr/bin/env python3
"""Collect a complete review snapshot through gh; never writes to GitHub."""
import argparse
import json
import re
import subprocess

PAGE = 'pageInfo { hasNextPage endCursor }'
COMMENTS = 'nodes { id url body author { login } } ' + PAGE
THREADS = ('nodes { id isResolved isOutdated path line comments(first:100) { ' + COMMENTS + ' } } ' + PAGE)


def gh(*args):
    result = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8', timeout=30)
    if result.returncode:
        raise ValueError('GitHub read failed: ' + result.stderr[-500:])
    if len(result.stdout) > 8 * 1024 * 1024:
        raise ValueError('GitHub response exceeds the collection budget')
    data = json.loads(result.stdout)
    if isinstance(data, dict) and data.get('errors'):
        raise ValueError('GitHub returned partial GraphQL data')
    return data


def connection_pages(first, fetch):
    result, ids, cursors = [], set(), set()
    page = first
    for _ in range(100):
        for node in page['nodes']:
            if node['id'] not in ids:
                result.append(node)
                ids.add(node['id'])
        info = page['pageInfo']
        if not info['hasNextPage']:
            return result
        cursor = info['endCursor']
        if not cursor or cursor in cursors:
            raise ValueError('incomplete pagination: cursor did not advance')
        cursors.add(cursor)
        page = fetch(cursor)
    raise ValueError('review pagination exceeds 100 pages; collection incomplete')


def collect(repository, number, client=gh):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository) or number < 1:
        raise ValueError('expected OWNER/REPO and a positive PR number')
    owner, repo = repository.split('/')
    endpoint = f'repos/{repository}/pulls/{number}'
    initial = client('api', endpoint)
    query = ('query($owner:String!,$repo:String!,$number:Int!,$cursor:String) {'
             ' repository(owner:$owner,name:$repo) { pullRequest(number:$number) {'
             ' reviewThreads(first:100,after:$cursor) { ' + THREADS + ' } } } }')

    def thread_page(cursor=None):
        args = ['api', 'graphql', '-f', 'query=' + query, '-f', 'owner=' + owner,
                '-f', 'repo=' + repo, '-F', 'number=' + str(number)]
        if cursor:
            args += ['-f', 'cursor=' + cursor]
        data = client(*args)
        if data.get('errors'):
            raise ValueError('partial GraphQL response')
        return data['data']['repository']['pullRequest']['reviewThreads']

    threads = connection_pages(thread_page(), thread_page)
    for thread in threads:
        def comment_page(cursor, thread_id=thread['id']):
            query = ('query($id:ID!,$cursor:String) { node(id:$id) { ... on PullRequestReviewThread {'
                     ' comments(first:100,after:$cursor) { ' + COMMENTS + ' } } } }')
            data = client('api', 'graphql', '-f', 'query=' + query, '-f', 'id=' + thread_id, '-f', 'cursor=' + cursor)
            if data.get('errors'):
                raise ValueError('partial thread response')
            return data['data']['node']['comments']
        thread['comments'] = connection_pages(thread['comments'], comment_page)

    def rest_pages(path):
        pages = client('api', '--paginate', '--slurp', path)
        if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
            raise ValueError('unexpected paginated response')
        return [item for page in pages for item in page]

    reviews = rest_pages(endpoint + '/reviews?per_page=100')
    comments = rest_pages(f'repos/{repository}/issues/{number}/comments?per_page=100')
    final = client('api', endpoint)
    if (initial['head']['sha'], initial['base']['sha']) != (final['head']['sha'], final['base']['sha']):
        raise ValueError('PR head/base changed during collection; read again')
    return dict(version=1, repository=repository, number=number, head=initial['head']['sha'],
                base=initial['base']['sha'], threads=threads, reviews=reviews, comments=comments,
                limits='Read snapshot, not an atomic review/CI snapshot or proof of resolution. Re-read before writes or merge.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', help='OWNER/REPO')
    parser.add_argument('number', type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(collect(args.repository, args.number), ensure_ascii=True, indent=2))
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        parser.exit(2, f'PR review collection incomplete: {error}\n')


if __name__ == '__main__':
    main()
