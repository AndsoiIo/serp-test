import random
import asyncio
import logging
import urllib.parse
import concurrent.futures

from sqlite3 import Cursor
from typing import Dict, Any, List, Optional
from aiohttp import ClientSession, TCPConnector, TraceConfig


def setup_client_logger():
    async def on_request_start(session, trace_config_ctx, params):
        trace_config_ctx.start = asyncio.get_event_loop().time()
        logging.debug('Request [%s] (%s), headers: %s', params.method, params.url, params.headers)

    async def on_request_end(session, trace_config_ctx, params):
        elapsed = asyncio.get_event_loop().time() - trace_config_ctx.start
        logging.debug(f'Response [%s] %d %s (%s) Take {elapsed:.3f} ms',
                      params.method, params.response.status, params.response.reason, params.url)

    trace_config = TraceConfig()
    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)

    return trace_config


class Scraper:

    def __init__(self, table: str, cursor: Cursor, user_agent: str = None, proxy: str = None):
        self.user_agent = user_agent
        self.proxy = proxy
        self.headers = {'User-Agent': self.user_agent}
        self._table = table
        self._cursor = cursor
        self._INSERT = f'INSERT into {self._table}(query, suggestion, type) values (?, ?, ?)'
        self._client: ClientSession = ClientSession(
            trace_configs=[setup_client_logger()],
        )
        self._loop: asyncio.BaseEventLoop = self._client.loop

    async def close(self):
        await self._client.close()

    async def _insert_one(self, q:str, item: Optional[List[str]], type_: Optional[str]):
        try:
            await self._loop.run_in_executor(
                None, self._cursor.execute, self._INSERT, (q, item, type_))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.exception(f'Some exceptions _insert_one.', exc_info=True)

    async def _insert_many(self, q: str, items: List[str], type_: str):
        data = ((q, item, type_) for item in items)
        try:
            # since sqlite3 may only be written to by one connection at a time
            # and the amount of data is incredibly small,
            # it probably doesn't make much sense to use threads...
            # ¯\_(ツ)_/¯ but we can
            await self._loop.run_in_executor(
                None, self._cursor.executemany, self._INSERT, data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logging.exception(f'Some exceptions _insert_many.', exc_info=True)

    def _clean(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        if not isinstance(data, dict):
            logging.debug('Wrong datatype, get %s instead dict.', type(data))
            return {}

        if 'products' in data: del data['products']
        categories = data.get('categories')
        if categories:
            data.update({'categories': [category['name'] for category in categories]})
        return data

    async def fetch_suggestions(self, query: str) -> Dict:
        url = 'https://allo.ua/ua/catalogsearch/ajax/suggest/?currentLocale=uk_UA'
        #  add some delay to be gentle with target server
        await asyncio.sleep(random.uniform(0.6, 1.6))

        self.headers.update({
            'Accept': "application/json",
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
        })
        raw_data = f"q={urllib.parse.quote(query)}&isAjax=1"
        async with self._client.post(url=url, proxy=self.proxy, headers=self.headers, data=raw_data, ssl=False) as resp:
            if resp.status != 200:
                return {}
            data = await resp.json(content_type=None)
            if isinstance(data, dict):
                return self._clean(data)

            return None

    async def fetch_data_and_save(self, query: str):
        data = []
        try:
            data = await self.fetch_suggestions(query)
        except Exception as e:
            logging.exception(f"Some exception fetch_data_and_save:", exc_info=True)
        if data:
            # type_ is 'query' or 'categories' str
            for type_ in data:
                await self._insert_many(query, data[type_], type_)
        else:
            await self._insert_one(query, None, None)
