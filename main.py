import sqlite3
from datetime import datetime
from hashlib import sha256
from random import randbytes

from flask import Flask, g, make_response, redirect, render_template, request

DATABASE = 'shopsoft.db' # database file name
DB_INIT = False # set to True to run init.sql script on startup

if DB_INIT:
    with open('init.sql', 'r') as script:
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        cursor.executescript(script.read())
        db.commit()
        db.close()

app = Flask(__name__)
sessions = {}

# INTERNAL

def getDB():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query(query, args=()):
    cur = getDB().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return rv

def generateSID(email):  # generate and associate session IDs and roles
    sid = sha256(randbytes(256) + email.encode()).hexdigest()
    sessions[sid] = email
    return sid

def validSession(sid):
    try:
        return sessions[request.cookies.get('sid')]
    except:
        return False

# WEB APPLICATION

@app.route('/', methods=('GET', 'POST'))
def login():
    error = None
    if request.method == 'POST':
        if (request.form['email'], 0) in query(
                'SELECT email, role FROM accounts WHERE hash=?;',
                args=(sha256(
                    request.form['password'].encode()).hexdigest(), )):
            resp = make_response(redirect('/catalog/'))
            resp.set_cookie('sid', generateSID(request.form['email']))
            return resp
        if (request.form['email'],) in query(
                'SELECT email FROM accounts WHERE hash=?;',
                args=(sha256(
                    request.form['password'].encode()).hexdigest(), )):
            resp = make_response(redirect('/staff/'))
            resp.set_cookie('sid', generateSID(request.form['email']))
            return resp
        error = 'Incorrect username or password.'
    return render_template('index.html', error=error)

@app.route('/register/', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        try:
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute(
                'INSERT INTO accounts(email, hash, role, name, address, phone, postalCode) VALUES(?, ?, ?, ?, ?, ?, ?);',
                (request.form['email'], sha256(
                    request.form['password'].encode()).hexdigest(), '0',
                request.form['name'], request.form['address'],
                request.form['phone'], request.form['postalCode']))
            cur.close()
            con.commit()
            con.close()
            error = True
        except:
            return render_template('register.html', error='An account with that information already exists.')
    return redirect('..')

@app.route('/inventory/', methods=('GET', 'POST'))
def inventory():
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    if (sessions[request.cookies.get('sid')],) not in query('SELECT email FROM accounts WHERE role=1 OR role=2'):
        return '<p>Your account does not have permission to access this feature. Click <a href=../../..>here</a> to return to the login page.</p>'
    if request.method == 'POST':
        try:
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute('INSERT INTO item(itemID, name, description, price, quantity, sold) VALUES(?, ?, ?, ?, ?, ?);',
                (request.form['itemID'],
                 request.form['itemName'],
                 request.form['description'],
                 request.form['price'],
                request.form['quantity'],
                0))
            cur.close()
            con.commit()
            con.close()
            return redirect('/staff/')
        except sqlite3.IntegrityError:
            cur.close()
            con.commit()
            con.close()
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute('DELETE FROM item WHERE itemID=?' (request.form['itemID'],))
            cur.close()
            con.commit()
            con.close()
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute('INSERT INTO item(itemID, name, description, price, quantity, sold) VALUES(?, ?, ?, ?, ?, ?)',
                (request.form['itemID'],
                 request.form['itemName'],
                 request.form['description'],
                 request.form['price'],
                request.form['quantity'],
                0))
            cur.close()
            con.commit()
            con.close()
            return redirect('/staff/')
        except:
            return render_template('inventory.html', error='Incomplete Information.')
    return render_template('inventory.html', error=None)

@app.route('/catalog/')
def catalog():
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    res = query('SELECT itemID, name FROM item')
    itemDict = {}
    for row in res:
        itemDict[row[0]] = row[1]
    return render_template('customer.html', itemDict=itemDict)

@app.route('/staff/')
def staff():
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    if (sessions[request.cookies.get('sid')],) not in query('SELECT email FROM accounts WHERE role=1'):
        return '<p>Your account does not have permission to access this feature. Click <a href=../../..>here</a> to return to the login page.</p>'
    res = query('SELECT itemID, name FROM item')
    itemDict = {}
    for row in res:
        itemDict[row[0]] = row[1]
    return render_template('staff.html', itemDict=itemDict)

@app.route('/inbox/')
def inbox():
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    return render_template('inbox.html', inbox=query('SELECT messageID, fromEmail, dateAndTime, subject FROM message WHERE toEmail=?', (sessions[request.cookies.get('sid')],)))

@app.route('/item/<itemID>/', methods=('GET', 'POST'))
def item(itemID):
    res = query(
        'SELECT name, description, price, quantity FROM item WHERE itemID=?',
        args=(itemID, ))
    if not res or res[0][3] < 1:
        return '<p><strong>Error:</strong> Item does not exist or is sold out.'
    if request.method == 'POST':
        try:
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute('INSERT INTO inCart(email, itemID, quantity) VALUES(?, ?, ?);',
                        (sessions[request.cookies.get('sid')], itemID, request.form['quantity']))
            cur.close()
            con.commit()
            con.close()
        except:
            pass
    res = res[0]
    imageURLs = query('SELECT imageURL FROM itemImageURL WHERE itemID=?',
                      (itemID, ))
    for i in range(0, len(imageURLs)):
        imageURLs[i] = imageURLs[i][0]
    return render_template(
        'item.html',
        name=res[0],
        description=res[1],
        price=res[2],
        imageURLs=imageURLs,
    )

@app.route('/item/<itemID>/like/')
def like(itemID):
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    if not query('SELECT itemID FROM item WHERE itemID=?', (itemID, )):
        return '<p><strong>Error:</strong> Item does not exist or is sold out.'
    try:
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        cur.execute('INSERT INTO likes(email, itemID) VALUES(?, ?);',
                    (sessions[request.cookies.get('sid')], itemID))
        cur.close()
        con.commit()
        con.close()
    except:
        cur.execute('DELETE FROM likes WHERE email=? AND itemID=?;',
                    (sessions[request.cookies.get('sid')], itemID))
        cur.close()
        con.commit()
        con.close()
    return redirect('..')

@app.route('/viewlikeditems/')
def viewLikedItems():
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    itemIDs = query('SELECT itemID FROM likes WHERE email=?', (sessions[request.cookies.get('sid')],))
    itemDict={}
    for i in range(0, len(itemIDs)):
        itemDict[itemIDs[i][0]] = query('SELECT name FROM item WHERE itemID=?', (itemIDs[i][0],))[0][0]
    return render_template('viewLikedItems.html', itemDict=itemDict)

@app.route('/customerinfo/')
def viewCustomerInfo():
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    if (sessions[request.cookies.get('sid')],) not in query('SELECT email FROM accounts WHERE role=1 OR role=2'):
        return '<p>Your account does not have permission to access this feature. Click <a href=../../..>here</a> to return to the login page.</p>'
    return render_template('customerInfo.html', table=query('SELECT email, name, address, postalCode, phone FROM accounts WHERE role=0'))

@app.route('/viewcart/', methods=('GET', 'POST'))
def viewCart():
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    itemIDs = query('SELECT itemID, quantity FROM inCart WHERE email=?', (sessions[request.cookies.get('sid')],))
    if itemIDs is None:
        return redirect('..')
    if request.method == 'POST':
        try:
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute('INSERT INTO purchase(email) VALUES(?)',(sessions[request.cookies.get('sid')],))
            cur.close()
            con.commit()
            con.close()
            purchaseID = query('SELECT MAX(purchaseID) FROM purchase')[0][0]
            for i in range(0, len(itemIDs)):
                con = sqlite3.connect(DATABASE)
                cur = con.cursor()
                cur.execute('INSERT INTO inPurchase(itemID, purchaseID, quantity) VALUES(?, ?, ?)',(itemIDs[i][0], purchaseID, itemIDs[i][1]))
                cur.close()
                con.commit()
                con.close()
                for row in query('SELECT email FROM accounts WHERE role=1'):
                    con = sqlite3.connect(DATABASE)
                    cur = con.cursor()
                    cur.execute(
                        "INSERT INTO message(content, subject, fromEmail, toEmail, dateAndTime) VALUES(?, ?, ?, ?, ?);",
                        (f"Item ID: {itemIDs[i][0]}\nQuantity: {itemIDs[i][1]}\nOrder Number: {purchaseID}" ,
                        f"Order #{purchaseID}",
                        sessions[request.cookies.get('sid')],
                        row[0],
                        datetime.now()))
                    cur.close()
                    con.commit()
                    con.close()
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute('DELETE FROM inCart WHERE email=?', (sessions[request.cookies.get('sid')],))
            cur.close()
            con.commit()
            con.close()
            return redirect('/catalog/')
        except:
            pass
    itemDict={}
    for i in range(0, len(itemIDs)):
        itemDict[itemIDs[i][0]] = query('SELECT name FROM item WHERE itemID=?', (itemIDs[i][0],))[0][0]
    return render_template('viewCart.html', itemDict=itemDict)

@app.route('/messagestaff/', methods=('GET', 'POST'))
def messageStaff():
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.</p>'
    if request.method == 'POST':
        for row in query('SELECT email FROM accounts WHERE role=1'):
            try:
                con = sqlite3.connect(DATABASE)
                cur = con.cursor()
                cur.execute(
                    'INSERT INTO message(content, fromEmail, subject, dateAndTime, toEmail) VALUES(?, ?, ?, ?, ?)',
                    (request.form['content'], 
                    request.form['subject'],
                    datetime.now(),
                    sessions[request.cookies.get('sid')],
                    row[0]))
                cur.close()
                con.commit()
                con.close()
            except:
                pass
        return redirect('/catalog/')
    return render_template('messageStaff.html')

@app.route('/message/', methods=('GET', 'POST'))
def message():
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    if (sessions[request.cookies.get('sid')],) not in query('SELECT email FROM accounts WHERE role=1 OR role=2'):
        return '<p>Your account does not have permission to access this feature. Click <a href=../../..>here</a> to return to the login page.</p>'
    if request.method == 'POST':
        try:
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute(
                "INSERT INTO message(content, subject, fromEmail, toEmail, dateAndTime) VALUES(?, ?, ?, ?, ?);",
                (request.form['content'],
                request.form['subject'],
                sessions[request.cookies.get('sid')],
                request.form['toEmail'],
                datetime.now()))
            cur.close()
            con.commit()
            con.close()
            return redirect('/staff/')
        except:
            pass
    return render_template('message.html')

@app.route('/message/<messageID>/')
def viewmessage(messageID):
    if not validSession(request.cookies.get('sid')):
        return '<p>Session Expired. Click <a href=../../..>here</a> to return to the login page.'
    if (sessions[request.cookies.get('sid')],) not in query('SELECT toEmail FROM message WHERE messageID=?', (messageID,)):
        return '<p>Your account does not have permission to access this message. Click <a href=../../..>here</a> to return to the login page.</p>'
    return render_template('viewMessage.html', message=query('SELECT fromEmail, subject, content FROM message WHERE messageID=?', (messageID,))[0])

app.run(host='0.0.0.0', port=5000, debug=True)
