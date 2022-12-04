#!/usr/bin/env python3.8
import os
from fdi.httppool import create_app  # , setup_logging
app = create_app()  # logger=logger)

if os.environ.get('APP_DEBUG', False) in (1, 'True'):
    from werkzeug.debug import DebuggedApplication
    app = DebuggedApplication(app, True)

application = app

if os.environ.get('UW_DEBUG', False) in (1, 'True'):
    from remote_pdb import RemotePdb
    RemotePdb('127.0.0.1', 4444).set_trace()

if __name__ == "__main__":
    app.run()
