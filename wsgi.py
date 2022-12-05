#!/usr/bin/env python3.8
#import os
from fdi.httppool import create_app  # , setup_logging
debug = False
app = create_app(debug=debug)  # logger=logger)

application = app


if __name__ == "__main__":
    app.run()
