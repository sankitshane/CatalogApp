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
from datetime import datetime

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
    categories = session.query(Categories).all()
    item = session.query(Item).all()
    return render_template('main.html', categories = categories, item = item)

@app.route('/catalog/<int:id>')
def Item_Catalog(id):
    categories = session.query(Categories).all()
    item = session.query(Item).filter_by(categories_id = id).all()
    return render_template('index.html', categories = categories, item = item)

@app.route('/catalog/<int:categories_id>/item/<int:id>')
def Item(id,categories_id):
    item = session.query(Item).filter_by(id = id).one()
    return render_template('item.html', item = item)

@app.route('/catalog/new/', methods = ['GET','POST'])
def newcategories():
    if request.method == 'POST':
        newcategorie = Categories(name = request.form['name'])
        session.add(newcategorie)
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        return render_template('newcat.html')

@app.route('/catalog/<int:id>/edit', methods = ['GET','POST'])
def editcategories(id):
    editedcategory = session.query(Categories).filter_by(id = id).one()
    if request.method == 'POST':
        editedcategory.name = request.form['name']
        return redirect(url_for('Catalog'))
    else:
        return render_template('newcat.html', category = editedcategory)

@app.route('/catalog/<int:id>/delete', methods = ['GET','POST'])
def delcategories(id):
    catelogtodelete = session.query(Categories).filter_by(id = id).one()
    if request.method == 'POST':
        session.delete(catelogtodelete)
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        return render_template('delete.html', category = catelogtodelete)

@app.route('/catalog/<int:categories_id>/new/', methods = ['GET','POST'])
def newItem(categories_id):
    if request.method == 'POST':
        newitem = Item(name = request.form['name'], description = request.form['description'], categories_id = categories_id)
        session.add(newitem)
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        return render_template('newcat.html')

@app.route('/catalog/<int:categories_id>/edit/<int:id>')
def editItem(categories_id,id):
    editeditem = session.query(Item).filter_by(id = id).one()
    if request.method == 'POST':
        editeditem.name = request.form['name']
        editeditem.description = request.form['description']
        return redirect(url_for('Catalog'))
    else:
        return render_template('newcat.html', item = editeditem)

@app.route('/catalog/<int:categories_id>/delete/<int:id>')
def delItem(categories_id,id):
    itemtodelete = session.query(Item).filter_by(id = id).one()
    if request.method == 'POST':
        session.delete(itemtodelete)
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        return render_template('delete.html', category = itemtodelete)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'

    app.debug = True
    app.run(host='0.0.0.0', port=5000)
