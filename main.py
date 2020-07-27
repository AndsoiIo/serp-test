import sys
import asyncio
import logging

from itertools import islice
from typing import List, Iterator
from concurrent.futures import ThreadPoolExecutor

from db import setup_db
from utils import prepare_queries, continue_from_last
from models import Scraper
from settings import settings_setup

ALPHA = 'абв' #  гдеёжзийклмнопрстуфхцчшщъыьэюя'


settings = settings_setup()
if True:
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(levelname)-8s %(message)s')

db = setup_db(settings.DB['name'])


async def run_clients_pool(queries: Iterator, clients: List[Scraper]):
    n = len(clients)
    gather = []
    tasks = []
    q = True
    while q:
        # take a few queries from queries generator
        q = list(islice(queries, 0, n))
        if not len(q):
            break
        # create task and send query from slice
        # you can think about it as a chunk
        # technically, we can create as many task as we want
        # and then execute them by gather to achieve full concurrency
        new_tasks = [clients[i].fetch_data_and_save(q[i]) for i in range(len(q))]
        tasks.extend(new_tasks)
        logging.debug("%s tasks added to gather", len(new_tasks))
        gather = await asyncio.gather(*tasks, return_exceptions=True)
    # replace gather while loop to full power :D if you if you are not afraid to had ban
    # gather = await asyncio.gather(*tasks, return_exceptions=True)
    return gather


async def main():
    gather = []
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
        gather = await run_clients_pool(queries, clients)
    except asyncio.CancelledError:
        asyncio.get_event_loop().run_until_complete(gather)
    except Exception as e:
        logging.exception('Main unhandled exception!')
    finally:
        [await client.close() for client in clients]

    print('All queries parsed...')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    PoolExecutor = ThreadPoolExecutor(max_workers=1)
    loop.set_default_executor(PoolExecutor)
    loop.create_task(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Cancelled.')
    finally:
        # graceful shutdown all awaited tasks
        tasks = asyncio.Task.all_tasks(loop=loop)
        for t in tasks:
            t.cancel()
        group = asyncio.gather(*tasks, return_exceptions=True)
        loop.run_until_complete(group)
        PoolExecutor.shutdown(wait=True)
        loop.close()