#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver
To run locally
    python server.py
Go to http://localhost:8111 in your browser
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for, flash, make_response, session
from flask_cache import Cache

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

cache = Cache(app,config={'CACHE_TYPE': 'simple'})


#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2

# DATABASEURI = "sqlite:///test.db"
DATABASEURI = "postgresql://ch3230:ary4d@104.196.175.120/postgres"

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
    # engine.execute("""DROP TABLE IF EXISTS test;""")
    # engine.execute("""CREATE TABLE IF NOT EXISTS test (
    #   id serial,
    #   name text
    # );""")
    # engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request
  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:
  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2
  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT account FROM Users")
  names = []
  for result in cursor:
    names.append(result[0])  # can also be accessed using result[0]
  cursor.close()
  print names

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
  return render_template("anotherfile.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print name
  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
  g.conn.execute(text(cmd), name1 = name, name2 = name);
  return redirect('/')

@app.route('/watch')
def watch():
  usr_account = session['acc']
  cursor = g.conn.execute("SELECT DISTINCT list_name FROM Users AS u, watchlist_own AS w \
                        WHERE u.account = w.account and u.account = %s", usr_account)
  cur = cursor.fetchall()
  print cur

@app.route('/signin', methods=['GET', 'POST'])
def signin():
  error = None
  watchlist = None
  cred = None
  search = None
  news = []
  if request.method == 'POST':
    usr = request.form['username'];
    pwd = request.form['password'];
    mail = request.form['email'];
    cursor = g.conn.execute("SELECT account FROM Users where name = %s", usr)
    cursor1 = g.conn.execute("SELECT password FROM Users WHERE name = %s", usr)
    cursor2 = g.conn.execute("SELECT s.edu_email FROM Users AS u, scholar AS s \
                   WHERE u.account = s.account and \
                   u.name = %s;", usr)
    cursor3 = g.conn.execute("SELECT list_name FROM Users AS u, watchlist_own AS w \
                   WHERE u.account = w.account and \
                   u.name = %s;", usr)
    cursor4 = g.conn.execute("SELECT a.news_id, a.list_name FROM add AS a, watchlist_own AS w \
                        WHERE w.list_name = a.list_name and a.list_name IN \
                        (SELECT list_name FROM Users AS u, watchlist_own AS w \
                        WHERE u.account = w.account and u.name = %s)", usr)
    
    cur1 = cursor1.first()
    cur2 = cursor2.first()
    cur3 = cursor3.fetchall()
    for n in cursor4:
      cursor5 = g.conn.execute("SELECT news_title, snippet_url FROM News WHERE news_id = %s", n['news_id'])
      cur5 = cursor5.first()
      news.append({str(n['list_name']): [cur5[0], cur5[1]]})

    if cur1 is None or cur2 is None:
      error = 'Invalid credentials. Please try again.'
    elif cur1[0] != pwd or cur2[0] != mail:
      error = 'Invalid credentials. Please try again.'
    else:
      search = 'success'
      watchlist = cur3
      cred = True
      session['acc'] = cursor.first()[0]
      watch()
      return render_template('signin.html', watchlist = watchlist, news = news, cred = cred, search = search, news_id = n['news_id'])
  return render_template('signin.html', error=error)


@app.route('/signinG', methods=['GET', 'POST'])
def signinG():
  error = None
  search = None
  if request.method == 'POST':
    usr = request.form['username'];
    pwd = request.form['password'];
    pho = request.form['phone'];
    cursor1 = g.conn.execute("SELECT password FROM Users WHERE name = %s", usr)
    cursor2 = g.conn.execute("SELECT phone_num FROM Users AS u, GeneralUsers AS gu \
                   WHERE u.account = gu.account and \
                   u.name = %s;", usr)
    cur1 = cursor1.first()
    cur2 = cursor2.first()
    if cur1 is None or cur2 is None:
      error = 'Invalid credentials. Please try again.'
    elif cur1[0] != pwd or cur2[0] != pho:
      error = 'Invalid credentials. Please try again.'
    else:
      search = 'success'
      return render_template('signinG.html', search = search)
  return render_template('signinG.html', error=error)  

@app.route('/register', methods = ['GET', 'POST'])
def register():
  error = None
  if request.method == 'POST':
    num = request.form['account_num'];
    usr = request.form['username'];
    pwd = request.form['password'];
    mail = request.form['email'];
    try:
      cursor1 = g.conn.execute("INSERT into users(account, name, password) values (%s, %s, %s)", (num, usr, pwd))
      cursor2 = g.conn.execute("INSERT into scholar(account, edu_email) values (%s, %s);",(num, mail))
    except Exception as e:
      error = e.message
      return render_template('register.html', error=error)
  
    return redirect(url_for('signin'))
  return render_template('register.html', error=error)

@app.route('/registerG', methods=['GET', 'POST'])
def registerG():
  error = None
  if request.method == 'POST':
    num = request.form['account_num'];
    usr = request.form['username'];
    pwd = request.form['password'];
    pho = request.form['phone'];
    try:
      cursor1 = g.conn.execute("INSERT into users(account, name, password) values (%s, %s, %s)", (num, usr, pwd))
      cursor2 = g.conn.execute("INSERT into generalusers(account, phone_num) values (%s, %s);",(num, pho))
    except Exception as e:
      error = e.message
      return render_template('registerG.html', error=error)
  
    return redirect(url_for('signinG'))

  return render_template('registerG.html', error=error)

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()

def is_query_safe(s):
  sql_statements = ['DROP TABLE', 'DROP DATABASE', 'DROP INDEX', 'DELETE TABLE']
  s = s.upper()

  for statement in sql_statements:
    if statement in s:
      return False

  return True

def call_recache():

  results_keywords = []
  results_categories = []

  #KEYWORDS
  cursor = g.conn.execute("SELECT p.word FROM keyword p")
  for result in cursor:
    results_keywords.append(result[0])
  print results_keywords
  cursor.close() 
  cache.set("keywords", results_keywords, timeout=300)


  #CATEGORIES
  cursor = g.conn.execute("SELECT p.category_name FROM category p")
  for result in cursor:
    results_categories.append(result[0])
  cursor.close() 
  cache.set("categories", results_categories, timeout=300)


# CHECK INPUT
@app.route('/search', methods=['GET', 'POST'])
def search():

  results_keywords = []
  results_categories = []

  if (cache.get("keywords") is None 
      or cache.get("categories") is None):
    call_recache()

  results_keywords= cache.get("keywords")
  results_titles = cache.get("titles")
  results_categories = cache.get('categories')
  return render_template("article_search.html", 
                            keywords=results_keywords 
                            , categories=results_categories)

@app.route('/search_keyword', methods=['GET'])
def search_keyword():

  query = request.args.get('query')

  # CHECK SAFE QUERY
  if not is_query_safe(query):
    msg = 'Stop trying to alter the database!'
    return render_template('error.html', error_msg=msg)
  cursor = g.conn.execute("SELECT News.* FROM News JOIN have ON News.news_id = have.news_id WHERE have.word = %s", query)
  rows = cursor.fetchall()
  cursor.close() 
  
  return render_template('article_results.html', keyword_data = rows)


@app.route('/search_category', methods=['GET'])
def search_category():

  query = request.args.get('query')
  # CHECK SAFE QUERY
  if not is_query_safe(query):
    msg = 'Stop trying to alter the database!'
    return render_template('error.html', error_msg=msg)
  cursor = g.conn.execute("SELECT News.* FROM News JOIN belong ON News.news_id = belong.news_id WHERE belong.category_name = %s", query)
  rows = cursor.fetchall()
  cursor.close() 
  
  return render_template('article_results.html', category_data = rows)

@app.route('/populate', methods=['GET'])
def populate_watchlist():
  usr_account = session['acc']

  cursor = g.conn.execute("SELECT DISTINCT list_name FROM Users AS u, watchlist_own AS w \
                        WHERE u.account = w.account and u.account = %s", usr_account)
  rows = []
  for result in cursor:
    rows.append(result[0])
  cursor.close() 


  return render_template('watchlist.html', watchlist_own = rows)

@app.route('/delete', methods=['GET', 'POST'])
def delete():
  usr_account = session['acc']
  list_name = request.args.get('list_name')
  news_id = request.args.get('news_id')
  #try:
  cursor = g.conn.execute("DELETE FROM add WHERE news_id=%s AND list_name=%s AND account=%s", (news_id, list_name, usr_account))
  #except Exception as e:
  #  return render_template('error.html')

  cursor.close() 
  return render_template('delete_success.html')


@app.route('/add_existing', methods=['GET', 'POST'])
def add_existing():
  usr_account = session['acc']
  query = request.args.get('query')
  news_id = request.args.get('news_id')
  try:
    cursor = g.conn.execute("INSERT into add(news_id, list_name, account) values (%s, %s, %s)", (news_id, query, usr_account))
  except Exception as e:
    return render_template('error.html')

  cursor.close() 
  return render_template('add_success.html')

@app.route('/add_new', methods=['GET'])
def add_new():
  return render_template('watchlist.html')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
    
  run()
