from chatbrick.view import facebook_get, facebook_post
from chatbrick.telegram_view import telegram_get, telegram_post


def setup_routes(app):
    app.router.add_get('/{name}/fb/', facebook_get)
    app.router.add_post('/{name}/fb/', facebook_post)
    app.router.add_get('/{name}/tg/', telegram_get)
    app.router.add_post('/{name}/tg/', telegram_post)

