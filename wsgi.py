#!/usr/bin/env python3
from fdi.httppool import create_app  # , setup_logging
app = create_app()  # logger=logger)
application = app

if __name__ == "__main__":
    app.run()
