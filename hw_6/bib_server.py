
# all imports
import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from pybtex.database import parse_string

app = Flask(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
ALLOWED_EXTENSIONS = set(['bib'])

# path of the database
default_db = os.path.join(app.root_path, 'bibtex.db')

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(default_db)
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def check_db_exist():
    """Check if a database already exists"""
    if os.path.isfile(default_db):
        flash('You have a database. Here are your collections:')
        return True
    else:
        flash('You do not yet have a database. A new database is created for you.')
        return False
    
def tidy_string(s):
    """Tidy up a string by removing braces and escape sequences"""
    s = s.replace("{", "").replace("}", "")
    return s.replace("\'", "").replace('\"', "").replace('\\','')


    
def make_author_list(entry):
    """produce a string from a pybtex.database.Entry object"""
    persons = entry.persons.values()[0]
    names = [str(p) for p in persons]
    s =  """, """.join(names)
    # remove curly braces and escape sequences
    return tidy_string(s)
    
def push_2_db(bibtex_str, collection_name, db_con):
    """push a collection to database"""
    
    bib_data = parse_string(bibtex_str, 'bibtex')
    cursor = db_con.cursor()
    
    # drop existing table if has the same name
    drop_cmd = """DROP TABLE IF EXISTS {}""".format(collection_name)
    cursor.execute(drop_cmd)
    db_con.commit()
    
    # first create table
    create_cmd = """CREATE TABLE {} (
    ref_tag TEXT PRIMARY KEY, author_list TEXT, journal TEXT,
    volume INTEGER, pages TEXT, year INTEGER, title TEXT, 
    collection TEXT) """.format(collection_name)
    
    cursor.execute(create_cmd)
    db_con.commit()
    
    # add each entry to the table
    for entry in bib_data.entries.values():
        entry_fields = entry.lower().fields.keys()
        wanted_fields = {'journal', 'volume','pages', 'year', 'title'}
        
        # valide fields
        valid_fields = []
        for fd in entry_fields:
            if fd in wanted_fields:
                valid_fields += [fd]
        
        ref_tag, author_list = entry.key, make_author_list(entry)
        
        # construct insert command
        # we only insert valid fields into database in case of missing data
        # so this takes a few lines to construct sql command
        bracket_1, bracket_2 = "{}", "\"{}\""
        bracket_dict = {'journal':bracket_2, 'volume':bracket_1,
                        'pages':bracket_2, 'year':bracket_1, 'title':bracket_2}
        valid_fd_str = ','.join(valid_fields)
        bracket_str = ','.join([bracket_dict[fd] for fd in valid_fields])
        valid_fd_values = list(tidy_string(entry.fields[fd]) for 
                               fd in valid_fields)
        
        insert_cmd = """INSERT INTO {} (ref_tag, author_list, """ + valid_fd_str + \
            """, collection) VALUES """ + """("{}", "{}","""+ bracket_str + """, "{}")"""
        insert_cmd = insert_cmd.format(collection_name, ref_tag, author_list, *valid_fd_values, collection_name)
        
        # commit insertion
        cursor.execute(insert_cmd)
        db_con.commit()        
    return

def get_tablenames():
    """get table names from database. """
    con = get_db()
    cursor = con.cursor()
    select_tn_cmd = "SELECT name FROM sqlite_master WHERE type='table';"
    tablenames, res = [], cursor.execute(select_tn_cmd).fetchall()
    for tn in res:
        tablenames += [tn['name']]
    return tablenames
    
@app.route("/")
def index():
    db_exist = check_db_exist()
    con = get_db()
    cursor = con.cursor()
    tablenames = get_tablenames()
    # get the number of entries for each table
    entrynum = []
    for item in tablenames:
        cmd = "SELECT * FROM {};".format(item)
        print(cmd)
        lines = cursor.execute(cmd).fetchall()
        entrynum += [len(lines)]
        
    return render_template("index.html", db_exist=db_exist, 
                           tablenames=tablenames, entrynum=entrynum)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/insert_collection", methods=['GET', 'POST'])
def insert_collection():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file is selected')
            return redirect(request.url)   
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        collection_name = request.form['collection_name']
        if not collection_name:
            flash('Please provide a collection name')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('Only .bib files are accepted')
            return redirect(request.url)
        try:
            bib_str = file.read().decode("utf-8")
        except Exception:
            flash('Unable to parse {}'.format(file.filename))
            return redirect(request.url)
        db_con = get_db()
        try:
            push_2_db(bib_str, collection_name, db_con)
        except Exception as e:
            flash("""An exception occurred in trying to 
                   push bibtex entries into data base.\n {}""".format(e))
            return redirect(request.url)
        return redirect(url_for('index'))
    return render_template('insert_collection.html')    

    
@app.route("/run_query", methods=['GET', 'POST'])
def run_query():
    """print form to collect query, and run query against database"""
    if request.method == 'POST':
        partial_query = request.form['partial_query']
        tablenames = get_tablenames()
        if not tablenames:
            flash("You don't have any collections yet. Please add a collection")
            return redirect(url_for("index"))
        
        sql_cmd = "SELECT * FROM {} WHERE ".format(" ".join(tablenames))
        sql_cmd += partial_query
        
        db_con = get_db()
        cursor = db_con.cursor()
        try:
            sql_entries = cursor.execute(sql_cmd).fetchall()
        except Exception as e:
            flash("Unrecognized query: {}".format(partial_query))
            flash("Please query again.")
            #return render_template('query.html', found_entry=False, sql_entries=[])
            return redirect(request.url)
        found_entry = True
        if not sql_entries:
            flash("No entries found")
            found_entry = False
        
        return render_template('query.html', found_entry=found_entry, sql_entries=sql_entries)
    return render_template('query.html', found_entry=False, sql_entries=[])

if __name__ == "__main__":   
    app.secret_key = 'super secret key'
    app.debug = True
    app.run()    
