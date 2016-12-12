from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Item
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
'''
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"
'''

@app.route('/')
@app.route('/catalog')
def Catalog():
    return "Main catalog page!"

@app.route('/catalog/<int:id>')
def Item_Catalog(id):
    return "Item related to specific item"

@app.route('/catalog/<int:id>/item/<int:categories_id>')
def Item(id,categories_id):
    return "Item description"

@app.route('/catalog/new/')
def newcategories():
    return "Page where you enter new categories!"

@app.route('/catalog/<int:id>/edit')
def editcategories(id):
    return "Page where you edit categories!"

@app.route('/catalog/<int:id>/delete')
def delcategories(id):
    return "Page where you delete categories!"

@app.route('/catalog/<int:categories_id>/new/')
def newItem(categories_id):
    return "Page where you create new Items!"

@app.route('/catalog/<int:categories_id>/edit/<int:id>')
def editItem(categories_id,id):
    return "Page where you edit Items!"

@app.route('/catalog/<int:categories_id>/delete/<int:id>')
def delItem(categories_id,id):
    return "Page where you delete Items!"

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
