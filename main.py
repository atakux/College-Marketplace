import requests
import googlemaps
import os
import bcrypt
import sqlalchemy as db

from flask import Flask, redirect, jsonify, request, render_template, url_for, flash
from sqlalchemy import text
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib, ssl



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

if not inspector.has_table("message"):
    engine.execute(
        "CREATE TABLE `message` ("
        "`message_id` INTEGER NOT NULL PRIMARY KEY,"
        "`sender_id` INTEGER NOT NULL,"
        "`receiver_id` INTEGER NOT NULL,"
        "`message_content` STRING NOT NULL,"
        "FOREIGN KEY (`sender_id`, `receiver_id`)"
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
def home():
    global user_data
    '''
    use render template to load the data into whatever the template is
    This is the list of items page where each item is on display
    '''
    #Get User Data if Logged in
    if is_logged_in():
        user = user_data
    else:
        user = False

    #Get item data
    results = None
    data = []
    with Session.begin() as session:
        results = session.execute(text('select * from item'))
        for r in results:
            r_dict = dict(r)
            r_dict['seller_name'] = get_seller_name_by_id(r_dict['seller_id'])
            data.append(r_dict)

    return render_template('home.html', item_list=data, user_data=user)

@app.route('/login', methods=['POST', 'GET'])
def login():
    global user_data

    if not is_logged_in():
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
                    return redirect('/')
            except Exception as ex:
                print("error" + str(ex))
        return render_template('signin.html')
    else:
        return redirect('/home')

@app.route('/logout')
def logout():
    global user_data
    if is_logged_in():
        user_data = None
    return redirect('/login')


# for testing
@app.route('/user')
def get_user_data():
    results = None
    data = []
    with Session.begin() as session:
        results = session.execute(text('select * from user'))
        for r in results:
            data.append(dict(r))
    return str(data)

# for testing
@app.route('/reviews')
def get_review_data():
    results = None
    data = []

    with Session.begin() as session:
        results = session.execute(text('select * from review'))
        for r in results:
            data.append(dict(r))
    return str(data)


@app.route('/sign_up', methods=['POST', 'GET'])
def sign_up():
    """
    Will be using a template. Likely will not need any input
    will need an output from the template in order to add the new user to the database
    """
    if not is_logged_in():
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
                return redirect('/login')
        return render_template('signup.html')
    else:
        return redirect('buy_sell')


@app.route('/buy_sell', methods=['GET', 'POST'])
def buy_sell():
    global user_data
    '''
    Display buy or sell page
    '''
    if is_logged_in():
        return render_template('buy_or_sell_page.html')
    else:
        return redirect('/login')

@app.route('/item/<int:id>')
def get_item(id: int):
    global user_data
    item_data = {}
    seller_data = {}

    if is_logged_in():
        with Session.begin() as session:
            item_results = session.execute(text('select * from item where item_id={}'.format(id)))
            for ir in item_results:
                item_data = dict(ir)
        with Session.begin() as session:
            seller_results = session.execute(text('select * from user where user_id={}'.format(item_data['seller_id'])))
            for sr in seller_results:
                seller_data = dict(sr)

        #Get place ids for locations
        user_place_id = (requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={user_data['user_zip']}&key={API_KEY}")).json()
        user_place_id = user_place_id['results'][0]["place_id"]
        seller_place_id = (requests.get(f"https://maps.googleapis.com/maps/api/geocode/json?address={seller_data['user_zip']}&key={API_KEY}")).json()
        seller_place_id = seller_place_id['results'][0]["place_id"]
        distance_matrix = (requests.get(f"https://maps.googleapis.com/maps/api/distancematrix/json?destinations={user_data['user_zip']}&origins={seller_data['user_zip']}&units=imperial&key={API_KEY}")).json()
        distance_miles = (distance_matrix['rows'][0]['elements'][0]['distance']['value'])//1609

        return render_template('itempage.html', item=item_data, seller=seller_data, user_zip=user_place_id, seller_zip=seller_place_id, distance=distance_miles, API_KEY=API_KEY)
    else:
        return redirect('/login')

@app.route('/send_email/<seller_id>', methods=['POST', 'GET'])
def send_email(seller_id: str):
    """Allows you send email to the user of associated id"""
    global user_data
    seller_data = {}
    buyer_data = {}

    if is_logged_in():
        print(seller_id)

        #Get Data
        with Session.begin() as session:
            seller_results = session.execute('select * from user where user_id={}'.format(seller_id))
            for sr in seller_results:
                seller_data = dict(sr)
            buyer_results = session.execute('select * from user where user_id={}'.format(user_data['user_id']))
            for br in buyer_results:
                buyer_data = dict(br)

        if request.method == 'POST':
            #Send Email
            #https://realpython.com/python-send-email/#option-1-setting-up-a-gmail-account-for-development
            subject = request.form.get('subject', '')
            message_text = request.form.get('message', '')

            sender_email = "collegemarketplace345@gmail.com"
            sender_password = "toubticyusplqrnd"
            receiver_email = seller_data['user_email']

            message = MIMEMultipart("alternative")
            message["Subject"] = f"CMP Message from {buyer_data['user_name']} - {subject}"
            message["From"] = sender_email
            message["To"] = receiver_email

            # Create the plain-text and HTML version of your message
            text = message_text
            html = """\
            <html>
            <body>
                <p>{}</p>
                <br>
                <p>To reply, please click this link: <a href="" target="_blank_"></a></p>
            </body>
            </html>
            """.format(message_text.replace('\n', "<br>"))
            print(text)
            print(html)

            # Turn these into plain/html MIMEText objects
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")

            # Add HTML/plain-text parts to MIMEMultipart message
            # The email client will try to render the last part first
            message.attach(part1)
            message.attach(part2)

            # Create secure connection with server and send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender_email, sender_password)
                server.sendmail(
                    sender_email, receiver_email, message.as_string()
                )
            return redirect('/buy_sell')
        else:
            return render_template('send_email.html', seller_data=seller_data, buyer_data=buyer_data)
    else:
        return redirect('/login')

@app.route('/send_report/<int:id>')
def send_report(id: int):
    global user_data

    if is_logged_in():
        reported_data = None
        with Session.begin() as session:
            reported_res = session.execute(text('select * from user where user_id={}'.format(id)))
            for repor in reported_res:
                reported_data = dict(repor)
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        msg = MIMEMultipart()
        msg['Subject'] = "User {} has been reported!!".format(reported_data["user_name"])
        # Login with your email and password
        smtp.login('collegemarketplace345@gmail.com', 'toubticyusplqrnd')

        # message to be sent
        txt = "{} has reported {}".format(user_data, reported_data)
        msg.attach(MIMEText(txt))

        # sending the mail
        smtp.sendmail("collegemarketplace345@gmail.com", "collegemarketplace345@gmail.com", msg.as_string())

        # Finally, don't forget to close the connection
        smtp.quit()
        return "report sent!!"
    else:
        return redirect('/login')

@app.route('/review/<int:id>', methods=["GET", "POST"])
def submit_review(id: int):
    global user_data
    if is_logged_in():
        connection = None
        id_num = 0
        if user_data is None:
            return redirect('/error')
        if request.method == 'POST':
            score = request.form.get('score', 'default score')
            rev_content = request.form.get('reviewContent', 'default content')
            engine.execute("INSERT INTO review (review_score, review_text, seller_id, user_id) "
            "VALUES (?, ?, ?, ?);", (int(score), rev_content, id, user_data["user_id"]))
        return render_template('review.html')
    else:
        return redirect('/login')



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
    if is_logged_in():
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
            "VALUES (?, ?, ?, ?, ?);", (item_name, price, description, user_data['user_id'], 1))
            photo = request.files['photo']
            filename = '{}.png'.format(id_num)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect('/home')
        return render_template('post_item.html')
    else:
        return redirect('/login')


@app.route('/chat/<int:id>', methods=['POST', 'GET'])
def message(id: int):
    global user_data
    msg_data = {}
    if request.method == 'POST':
        msg_content = request.form.get('messageContent', 'default content')
        engine.execute("INSERT INTO message (sender_id, receiver_id, message_content) VALUES (?, ?, ?);",
        (user_data["user_id"], id, msg_content))
    elif request.method == 'GET':
        with Session.begin() as session:
            msg_results = session.execute(text("SELECT message_content FROM message WHERE receiver_id "
                                               "= {} ".format(user_data['user_id'])))
            sender_results = session.execute(text("SELECT user_name FROM user WHERE user_id = "
                                                  "{}".format(id)))
            receiver_results = session.execute(text("SELECT user_name FROM user WHERE user_id = "
                                                    "{}".format(user_data['user_id'])))
            senders = {}
            receivers = {}
            for msg in msg_results:
                msg_data = dict(msg)
            for sends in sender_results:
                senders = dict(sends)
            for recs in receiver_results:
                receivers = dict(recs)
            values = []
            for key, val in msg_data.items():
                values.append(val)
            for key, val in senders.items():
                the_sender = val
            for key, val in receivers.items():
                the_receiver = val
            print(values)
            print(senders)
        return render_template('message.html', receiver=the_receiver, sender=the_sender, messages=values)
    return render_template('message.html')


@app.route('/error')
def display_error():
    return render_template('error.html')


def is_logged_in():
    global user_data
    """Checks to see if user is logged in. If so, returns true. If not, returns false"""
    try:
        if user_data is None:
            return False
        else:
            return True
    except NameError:
        return False

def get_seller_name_by_id(id):
    with Session.begin() as session:
            seller_results = session.execute(text('select * from user where user_id={}'.format(id)))
            for sr in seller_results:
                return sr['user_name']


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
