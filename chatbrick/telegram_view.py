import logging
import asyncio
import traceback

from aiohttp import web

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def telegram_get(request):
    data = request.query
    logger.info(data)
    return web.Response(text='null', status=404)

async def telegram_post(request):
    data = request.query
    logger.info(data)
    return web.Response(text='null', status=404)