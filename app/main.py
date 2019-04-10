import plac
import uvicorn
from starlette.applications import Starlette
from starlette.config import Config
from starlette.graphql import GraphQLApp
from starlette.middleware.gzip import GZipMiddleware

from app.schema.schema import schema

# Config will be read from environment variables and/or ".env" files.
config = Config(".env")

DEBUG = config('DEBUG', cast=bool, default=False)
APP_PORT = config('APP_PORT', cast=int, default=8990)
APP_HOST = config('APP_HOST', cast=str, default='0.0.0.0')
APP_LOG_LEVEL = config('APP_LOG_LEVEL', cast=str, default="info")

app = Starlette(debug=DEBUG)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.on_event('startup')
def startup():
    print('Ready to go')


@app.on_event('shutdown')
def shutdown():
    print('Shutting down')


app.add_route("/", GraphQLApp(schema))


@app.route("/schema")
def read_schema():
    return schema.introspect()


def main(
        log_level: (
                "Set the log level", "option", None, str,
                ['critical', 'error', 'warning', 'info', 'debug']) = APP_LOG_LEVEL,
        port: ("Bind to a socket with this port", "option", "p", int) = APP_PORT,
        host: (
                "Bind socket to this host. Use 0.0.0.0 to make the application available on your local network",
                "option", "s",
                str) = APP_HOST):
    uvicorn.run(app, host=host, port=port, debug=DEBUG, log_level=log_level)


if __name__ == "__main__":
    plac.call(main)
