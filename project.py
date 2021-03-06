from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CItem, User
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

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    """
    Creates a random generated number and sets it as state.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """
    Code to validate, fetch and use data from Facebook Oauth
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = """https://graph.facebook.com/oauth/access_token?
            grant_type=fb_exchange_token&client_id=%s&client_secret=%s
            &fb_exchange_token=%s""" % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.8/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]
    """
    The token must be stored in the login_session in order to properly
    logout,let's strip out the information before the equals sign in our token
    """
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = """https://graph.facebook.com/v2.8/me/picture?%s&
            redirect=0&height=200&width=200""" % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """ " style = "width: 200px; height: 200px;border-radius: 100px;
    -webkit-border-radius: 100px;-moz-border-radius: 100px;"> """
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    """
    To Delete data from Facebook
    """
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = """https://graph.facebook.com/%s/permissions?
            access_token=%s""" % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Code to validate, fetch and use data from Google Oauth
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """ " style = "width: 200px; height: 200px;border-radius: 100px;
                -webkit-border-radius: 100px;-moz-border-radius: 100px;"> """
    print "done!"

    print login_session
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    """
    To Delete data from Google
    """
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Catalog Information
@app.route('/catalog/JSON/')
def categoriesJSON():
    categories = session.query(Category).all()
    items = session.query(CItem).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/catalog/<int:id>/catalog.json')
def itemJSON(id):
    item = session.query(CItem).filter_by(id = id).all()
    return jsonify(item = [i.serialize for i in item])


@app.route('/')
@app.route('/catalog')
def Catalog():
    categories = session.query(Category).all()
    items = session.query(CItem).all()
    if 'username' not in login_session:
        return render_template('main.html',
                                categories=categories,
                                items=items,
                                login="false")
    else:
        return render_template('main.html',
                                categories=categories,
                                items=items,
                                info=login_session,
                                login="true")


@app.route('/catalog/<string:name>/items')
def Item_Catalog(name):
    categories = session.query(Category).all()
    cat_id = session.query(Category).filter_by(name=name).one()
    items = session.query(CItem).filter_by(categories_id=cat_id.id).all()
    if 'username' not in login_session:
        return render_template('main.html',
                                categories=categories,
                                items=items,
                                login="false")
    else:
        return render_template('main.html',
                                categories=categories,
                                items=items,
                                info=login_session,
                                login="true")


@app.route('/catalog/<string:name>/<string:i_name>')
def Item(name, i_name):
    item = session.query(CItem).filter_by(name=i_name).one()
    if 'username' not in login_session:
        return render_template('item.html', item=item, login="false")
    else:
        return render_template('item.html', item=item, login="true")


@app.route('/catalog/new/', methods=['GET', 'POST'])
def newcategories():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newcategorie = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newcategorie)
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        if 'username' not in login_session:
            return render_template('newcat.html', type="cat", login="false")
        else:
            return render_template('newcat.html', type="cat", login="true")


@app.route('/catalog/<string:name>/editcategory', methods=['GET', 'POST'])
def editcategories(name):
    editedcategory = session.query(Category).filter_by(name=name).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedcategory.user_id != login_session['user_id']:
        return """<script>function myFunction() {alert('You are not authorized
                to edit this Catalog. Please create your own Catalog in order
                 to edit.');}</script><body onload='myFunction()''>"""
    if request.method == 'POST':
        editedcategory.name = request.form['name']
        return redirect(url_for('Catalog'))
    else:
        if 'username' not in login_session:
            return render_template('newcat.html',
                                    category=editedcategory,
                                    type="cat",
                                    login="false")
        else:
            return render_template('newcat.html',
                                    category=editedcategory,
                                    type="cat",
                                    login="true")


@app.route('/catalog/<string:name>/deletecategory', methods=['GET', 'POST'])
def delcategories(name):
    catelogtodelete = session.query(Category).filter_by(name=name).one()
    if 'username' not in login_session:
        return redirect('/login')
    if catelogtodelete.user_id != login_session['user_id']:
        return """<script>function myFunction() {alert('You are not authorized
                to delete this Catalog. Please create your own Catalog in order
                 to delete.');}</script><body onload='myFunction()''>"""
    if request.method == 'POST':
        session.delete(catelogtodelete)
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        if 'username' not in login_session:
            return render_template('delete.html',
                                    category=catelogtodelete,
                                    login="false")
        else:
            return render_template('delete.html',
                                    category=catelogtodelete,
                                    login="true")


@app.route('/catalog/newitem/', methods=['GET', 'POST'])
def newItem():
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        cat_id = session.query(Category).filter_by(
            name=request.form['category']).one()
        newitem = CItem(name=request.form['name'],
                        description=request.form['description'],
                        categories_id=cat_id.id,
                        user_id=login_session['user_id'])
        session.add(newitem)
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        if 'username' not in login_session:
            return render_template('newcat.html',
                                    categories=categories,
                                    login="false")
        else:
            return render_template('newcat.html',
                                    categories=categories,
                                    login="true")


@app.route('/catalog/<string:name>/edit/', methods=['GET', 'POST'])
def editItem(name):
    editeditem = session.query(CItem).filter_by(name=name).one()
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return redirect('/login')
    if editeditem.user_id != login_session['user_id']:
        return """<script>function myFunction() {alert('You are not authorized
                to edit this Catalog. Please create your own Catalog in order
                to edit.');}</script><body onload='myFunction()''>"""
    if request.method == 'POST':
        editeditem.name = request.form['name']
        editeditem.description = request.form['description']
        cat = session.query(Category).filter_by(
            name=request.form['category']).one()
        editeditem.categories_id = cat.id
        return redirect(url_for('Catalog'))
    else:
        if 'username' not in login_session:
            return render_template('newcat.html',
                                    item=editeditem,
                                    categories=categories,
                                    login="false")
        else:
            return render_template('newcat.html',
                                    item=editeditem,
                                    categories=categories,
                                    login="true")


@app.route('/catalog/<string:name>/delete/', methods=['GET', 'POST'])
def delItem(name):
    itemtodelete = session.query(CItem).filter_by(name=name).one()
    if 'username' not in login_session:
        return redirect('/login')
    if itemtodelete.user_id != login_session['user_id']:
        return """<script>function myFunction() {alert('You are not authorized
                to delete this Catalog. Please create your own Catalog in order
                 to delete.');}</script><body onload='myFunction()''>"""
    if request.method == 'POST':
        session.delete(itemtodelete)
        session.commit()
        return redirect(url_for('Catalog'))
    else:
        if 'username' not in login_session:
            return render_template('delete.html',
                                    category=itemtodelete,
                                    login="false")
        else:
            return render_template('delete.html',
                                    category=itemtodelete,
                                    login="true")


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        del login_session['_flashes']
        print login_session
        return redirect(url_for('Catalog'))

    else:
        return redirect(url_for('Catalog'))

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
