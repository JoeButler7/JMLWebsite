#!/usr/bin/env python

import os
from flask import Flask, render_template, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, NumberRange
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)











if __name__ == '__main__':
  app.run( debug=True)
