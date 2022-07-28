import requests
import googlemaps
import os
import bcrypt
import sqlalchemy as db

from flask import Flask, redirect, jsonify, request, render_template, url_for, flash

# commented below bc it dont lemme run bc of some wekrzeug seucirty thing
# from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user

from sqlalchemy import text
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib



Base = declarative_base()

engine = db.create_engine('sqlite:///buy_sell_database.sql')

meta = MetaData()
meta.reflect(bind=engine, views=True)
inspector = db.inspect(engine)
if not inspector.has_table("user"):
    engine.execute(
        "CREATE TABLE `user` ("
        "`user_id` INTEGER NOT NULL PRIMARY KEY,"
        "`user_name` TEXT NOT NULL,"
        "`user_email` TEXT NOT NULL,"
        "`user_zip` TEXT NOT NULL,"
        "`user_password` TEXT NOT NULL"
        ")")

if not inspector.has_table("item"):
    engine.execute(
        "CREATE TABLE `item` ("
        "`item_id` INTEGER NOT NULL PRIMARY KEY,"
        "`item_name` TEXT NOT NULL,"
        "`item_price` TEXT NOT NULL,"
        "`item_description` TEXT NOT NULL,"
        "`seller_id` INTEGER NOT NULL,"
        "`active` INTEGER NOT NULL,"
        "FOREIGN KEY (`seller_id`)"
        "   REFERENCES user (user_id)"
        ")")

if not inspector.has_table("review"):
    engine.execute(
        "CREATE TABLE `review` ("
        "`review_id` INTEGER NOT NULL PRIMARY KEY,"
        "`review_score` INTEGER NOT NULL,"
        "`review_text` TEXT NOT NULL,"
        "`seller_id` INTEGER NOT NULL,"
        "`user_id` INTEGER NOT NULL,"
        "FOREIGN KEY (`seller_id`, `user_id`)"
        "   REFERENCES user (user_id, user_id)"
        ")")

#Flask
app = Flask(__name__)
API_KEY = os.environ['API_KEY']
UPLOAD_FOLDER = 'static/images'
app.config['SECRET_KEY'] = 'fec93d1b1cb7926beb25960608b25818'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
map_client = googlemaps.Client(API_KEY)
Session = sessionmaker(engine)

@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
def login():
    global user_data

    if request.method == 'POST':
        email = request.form.get('email', 'default value email')
        password = request.form.get('password', 'default value password')
        try:
            user_results = None
            with Session.begin() as session:
                user_results = session.execute(text("select * from user where user_email='{}'".format(str(email))))
                for r in user_results:
                    user_data = dict(r)
            if bcrypt.checkpw(bytes(password, encoding='utf8'), user_data['user_password']):
                print("successful login")
                return redirect(url_for('buy_sell'))
        except Exception as ex:
            print("error" + str(ex))
    return render_template('signin.html')


# for testing
@app.route('/user')
def get_table_data():
    results = None
    data = []

    with Session.begin() as session:
        results = session.execute(text('select * from user'))
        for r in results:
            data.append(dict(r))
    return str(data)


@app.route('/sign_up', methods=['POST', 'GET'])
def sign_up():
    """
    Will be using a template. Likely will not need any input
    will need an output from the template in order to add the new user to the database
    """
    if request.method == 'POST':
        user_name = request.form.get('userName', 'default value name')
        email = request.form.get('email', 'default value email')

        if '.edu' not in email:
            print("invalid email")
            flash("You must input a school email.")
            return render_template('signup.html')
        else:
            password = request.form.get('password', 'default value password')
            address = request.form.get('address', 'default address')

            salt = bcrypt.gensalt()
            hashed_pass = bcrypt.hashpw(bytes(password, encoding='utf8'), salt)

            engine.execute("INSERT INTO user (user_name, user_email, user_zip, "
                           "user_password) VALUES (?, ?, ?, ?);",
                           (user_name, email, address, hashed_pass))
            return redirect('/')
    return render_template('signup.html')


@app.route('/buy_sell', methods=['GET', 'POST'])
def buy_sell():
    global user_data
    '''
    Display buy or sell page
    '''
    if user_data is None:
        return redirect('/error')
    return render_template('buy_or_sell_page.html')


@app.route('/buy')
def list_of_items():
    global user_data
    '''
    use render template to load the data into whatever the template is
    This is the list of items page where each item is on display
    '''
    if user_data is None:
        return redirect('/error')
    results = None
    data = []
    with Session.begin() as session:
        results = session.execute(text('select * from item'))
        for r in results:
            data.append(dict(r))
    return render_template('list_of_items_page.html', item_list=data)


@app.route('/item/<int:id>')
def get_item(id: int):
    global user_data
    item_data = {}
    seller_data = {}
    if user_data is None:
        return redirect('/error')
    with Session.begin() as session:
        item_results = session.execute(text('select * from item where item_id={}'.format(id)))
        for ir in item_results:
            item_data = dict(ir)
    with Session.begin() as session:
        seller_results = session.execute(text('select * from user where user_id={}'.format(item_data['seller_id'])))
        for sr in seller_results:
            seller_data = dict(sr)
    return render_template('itempage.html', item=item_data, seller=seller_data, user_address=user_data['user_zip'])

@app.route('/send_email/<email>')
def send_email(email: str):
    print(email)
    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.ehlo()
    smtp.starttls()
    
    # Login with your email and password
    smtp.login('collegemarketplace345@gmail.com', 'toubticyusplqrnd')
    
    # message to be sent
    message = "Item to be sold"
    
    # sending the mail
    smtp.sendmail("collegemarketplace345@gmail.com", email, message)
    
    # Finally, don't forget to close the connection
    smtp.quit()
    return "bean"

@app.route('/sell', methods=['POST', 'GET'])
def sell_item():
    global user_data
    connection = None
    '''
    Will be using a template. Likely will not need any input
    will need an output from the template in order to add the new item to the database
    
    if request.method == 'POST':
        user = request.form
        return 'adding item please wait a moment'''
    if user_data is None:
        return redirect('/error')
    if request.method == 'POST':
        item_name = request.form.get('name', 'default item name')
        price = request.form.get('price', 'default price')
        description = request.form.get('itemDesc', 'default description')
        id_num = 0
        try:
            connection = engine.connect()
            cursor = connection.execute("SELECT count(*) from item;")
            result = cursor.scalar()
            id_num = int(result) + 1
        except:
            print("something went wrong")
        finally:
            if not connection.closed:
                cursor.close()
                connection.close()
        engine.execute("INSERT INTO item (item_name, item_price, item_description, seller_id, active) "
        "VALUES (?, ?, ?, ?, ?);", (item_name, price, description, user_data['user_id'], True))
        photo = request.files['photo']
        filename = '{}.png'.format(id_num)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return render_template('post_item.html')


@app.route('/error')
def display_error():
    return render_template('error.html')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
