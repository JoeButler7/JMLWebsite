#!/usr/bin/env python
from Site import app, init_db

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
