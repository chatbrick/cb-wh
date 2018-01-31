import os
from chatbrick import app, web
from aiohttp_utils import run


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8002))
    web.run_app(app, host='127.0.0.1', port=port)
    # run(app, host='127.0.0.1', app_uri='chatbrick:app', port=port, reload=True)
