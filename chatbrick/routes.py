from chatbrick.view import facebook_get, facebook_post, refresh_post
from chatbrick.telegram_view import telegram_get, telegram_post
from chatbrick.api import request_api


def setup_routes(app):
    app.router.add_get('/webhooks/{name}/fb/', facebook_get)
    app.router.add_post('/webhooks/{name}/fb/', facebook_post)
    app.router.add_get('/webhooks/fb/', facebook_get)
    app.router.add_post('/webhooks/fb/', facebook_post)
    app.router.add_get('/webhooks/{name}/tg/', telegram_get)
    app.router.add_post('/webhooks/{name}/tg/', telegram_post)
    app.router.add_post('/webhooks/refresh/{name}/', refresh_post)
    app.router.add_get('/webhooks/api/telegram/{api}/', request_api)
