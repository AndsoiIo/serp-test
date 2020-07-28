import sys
import asyncio
import logging

from itertools import islice
from typing import List, Iterator
from concurrent.futures import ThreadPoolExecutor, CancelledError

from db import setup_db
from utils import prepare_queries, continue_from_last
from models import Scraper
from settings import settings_setup

ALPHA = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'


settings = settings_setup()
if settings.DEBUG:
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(levelname)-8s %(message)s')

db = setup_db(settings.DB)


async def run_clients_pool(queries: Iterator, clients: List[Scraper]):
    n = len(clients)
    tasks = []
    q = True
    while q:
        # take a few queries from queries iterator
        q = list(islice(queries, 0, n))
        print(f"Parse queries: {', '.join(q)}...")
        if not len(q):
            break
        # create task and send query from slice
        # you can think about it as a chunk
        # technically, we can create as many task as we want
        # and then execute them by gather to achieve full concurrency
        new_tasks = [clients[i].fetch_data_and_save(q[i]) for i in range(len(q))]
        tasks.extend(new_tasks)
        logging.debug("%s tasks added to gather", len(new_tasks))
        await asyncio.gather(*tasks, return_exceptions=True)
    # replace gather while loop to full cocurrency power :D if you are not afraid to get banned
    # gather = await asyncio.gather(*tasks, return_exceptions=True)


async def main():
    clients = []
    queries = prepare_queries(ALPHA)

    if not settings.OVERWRITE:
        queries = continue_from_last(db, settings.DB['table'], queries)

    for user_agent in settings.USER_AGENTS:
        proxy = None
        if settings.PROXIES:
            proxy = settings.PROXIES.pop()
        client = Scraper(settings.DB['table'], db.cursor(), user_agent, proxy=proxy)
        clients.append(client)

    try:
        await run_clients_pool(queries, clients)
    except Exception as e:
        logging.exception('Main unhandled exception!')
    finally:
        [await client.close() for client in clients]

    print('All queries parsed...')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    PoolExecutor = ThreadPoolExecutor(max_workers=1)
    loop.set_default_executor(PoolExecutor)
    try:
        loop.run_until_complete(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print('Cancelled.')
    finally:
        # gracefully shutdown all awaited tasks
        tasks = asyncio.Task.all_tasks()
        [t.cancel() for t in tasks]
        # loop.run_until_complete(asyncio.gather(*tasks))
        PoolExecutor.shutdown(wait=True)
        loop.close()
