from os import path


class Config(object):
    APP_DIR = path.dirname(path.abspath(__file__))
    BASE_DIR = path.dirname(APP_DIR)
    DEBUG = True
    SECRET_KEY = 'j43780upoy28ewrhjkeru0904780werf'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{base_dir}/db.sqlite3'.format(base_dir=BASE_DIR)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER='smtp.gmail.com'
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USERNAME = 'overRated.UR'
    MAIL_PASSWORD= 'JML12345'
