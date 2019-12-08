from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_dotenv import DotEnv
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_scss import Scss
from flask_mail import Mail

from .config import Config

app = Flask(__name__)
Scss(app)
app.config.from_object(Config)
env = DotEnv(app)
mail = Mail(app)

csrf = CSRFProtect(app)

from .db import init_db  # noqa: F401, E402
from .models import User  # noqa: E402
from .models import Post  # noqa: E402
from .models import PostLike  # noqa: E402
from .models import Likers  # noqa: E402

login_manager = LoginManager()
login_manager.user_loader(User.load_user)
login_manager.init_app(app)

from . import routes
