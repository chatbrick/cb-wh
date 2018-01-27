from chatbrick.view import facebook_get, facebook_post
from chatbrick.telegram_view import telegram_get, telegram_post


def setup_routes(app):
    app.router.add_get('/webhooks/{name}/fb/', facebook_get)
    app.router.add_post('/webhooks/{name}/fb/', facebook_post)
    app.router.add_get('/webhooks/fb/', facebook_get)
    app.router.add_post('/webhooks/fb/', facebook_post)
    app.router.add_get('/webhooks/{name}/tg/', telegram_get)
    app.router.add_post('/webhooks/{name}/tg/', telegram_post)
