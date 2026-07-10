

import pytest
from web_conductor.certs import certs_process_domains

test_domains = [
    'example.com',
    'xyz.example.com',
    'abc.example.com',

    'example.org',
    'sub0.example.org',
    'sub1.example.org',
    'sub2.example.org',
    '0.sub2.example.org',
    '1.sub2.example.org',
    'x.1.sub2.example.org',
    'y.1.sub2.example.org',
    'z.1.sub2.example.org',

    # sorted by level, expect example.net before example.org
    '2.a.b.c.example.net',
    '1.a.b.c.example.net',
    '0.a.b.c.example.net',

    'test0.localhost',
    'a.test1.localhost',
    'b.test1.localhost',

    # duplicates are removed
    'xyz.example.com',
    'example.org',
]


@pytest.mark.parametrize(
    'generate_wildcards', [True, False]
)
def test_process_domains(snapshot, generate_wildcards):
    assert certs_process_domains(test_domains, generate_wildcards=generate_wildcards) == snapshot()
