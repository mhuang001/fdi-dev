#!/usr/bin/env python3.8
import os
from fdi.httppool import create_app  # , setup_logging
app = create_app()  # logger=logger)

if 'APP_DEBUG' in os.environ:
    from werkzeug.debug import DebuggedApplication
    app = DebuggedApplication(app, True)

application = app

if 'UW_DEBUG' in os.environ:
    from remote_pdb import RemotePdb
    RemotePdb('127.0.0.1', 4444).set_trace()

if __name__ == "__main__":
    app.run()
