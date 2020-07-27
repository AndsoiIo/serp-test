import sys
import operator
import logging

from sqlite3 import Connection
from functools import reduce
from itertools import product, chain, islice
from typing import Iterator


def prepare_queries(alpha) -> Iterator:
    # make lazy list of all possible combinations of our queries
    full_tuple_queries = chain(
        product(alpha),         # generator( ('a',), ('b',), ... ('z',) )
        product(*[alpha] * 2),  # generator( ('a', 'a'), ('a', 'b'), ... )
        product(*[alpha] * 3)   # generator( ('a', 'a', 'a'), ... )
    )
    logging.debug('Current "alpha" is "%s"', alpha)

    return map(lambda t: reduce(operator.add, t), full_tuple_queries)


def continue_from_last(db: Connection, table: str, queries: Iterator) -> Iterator:
    cursor = db.cursor()
    cursor.execute(f"SELECT DISTINCT query FROM {table} ORDER BY query DESC LIMIT(1)")
    last = cursor.fetchone()
    cursor.close()

    if not last:
        return queries

    lst = list(queries)
    last = ''.join(last)
    index = lst.index(last)
    logging.debug('Last query string is "%s", on %d index out of %d', last, index, len(lst))
    return islice(lst, index, sys.maxsize)
