#! /usr/bin/python3.6

from fdi.httppool import create_app  # , setup_logging
app = create_app()  # logger=logger)

if __name__ == "__main__":
    app.run()
