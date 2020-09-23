from flask import Flask, request, render_template, url_for, flash, session,redirect,jsonify
import pymysql,sys,datetime,os

from werkzeug.security import generate_password_hash, check_password_hash

HOST = 'localhost'
USER = 'lcc'
PASSWORD = 'lccsjce'
DATABASE = 'vfm'

db = pymysql.connect(host=HOST,user=USER,password=PASSWORD,db=DATABASE)
                            
if db.open:
    print("Connection established to database successfully")
else:
    print("Connection failed")
    sys.exit('Database connection error')
    
from forms import LoginForm

app = Flask(__name__)

app.config['SECRET_KEY'] = 'LCCSJCE'

dept = []
cursor = db.cursor()
cursor.execute('SELECT dept_id,dept_name FROM departments')
departments_data = cursor.fetchall()
cursor.close()

for dep in departments_data:
    dept.append(dep)

print(dept)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form=LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if check_password_hash('sha256$eYob2HNe$3e550352223c7bd17134b2830b33370f1db41d4a836fa4474ae5da2889dea368', form.password.data):
                        session['loggedin'] = True
                        session['username'] = 'Admin'
                        session['admin'] = True
                        flash("Login successful!!","success")
                        return redirect(url_for('.admin_homepage'))
            with db.cursor() as conn:
                conn.execute('SELECT * FROM departments WHERE dept_name = %s', (form.username.data,))
                user = conn.fetchone()
            if user:
                if check_password_hash(user[3], form.password.data):
                    session['loggedin'] = True
                    session['id'] = user[0]
                    session['username'] = user[1]
                    flash("Login successful!!","success")
                    return redirect(url_for('.dashboard'))
                else:
                    flash("Invalid username or password", "danger")
            else:
                flash("Invalid username or password", "danger")
    return render_template('loginpage.html', form=form,dept=dept) 

@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', logout=url_for('.logout'))

@app.route('/history')
def history():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    
    return render_template('options.html',back=url_for('.dashboard'), logout=url_for('.logout'))

@app.route('/history/<status>')
def display_history(status):

    if not session.get('loggedin'):
        return redirect(url_for('login'))

    current_dept = session.get('username')
    history_requests = {}

    

    #get all the requests
    sql_query =  '''SELECT timestamp,from_dept,to_dept,file_id,description,tran_id
                    FROM transactions
                    WHERE from_dept = %s and status = %s
                    ORDER BY timestamp DESC
    '''

    
    cursor = db.cursor()
    cursor.execute(sql_query,(current_dept,status,))
    history_transactions_data = cursor.fetchall()
    cursor.close()
    
    for transactions in history_transactions_data:
        file_history = []
        file_name = transactions[3]

        sql_query =  '''SELECT from_dept,to_dept,status
                    FROM transactions
                    WHERE file_id = %s
                    ORDER BY timestamp
        '''

        cursor = db.cursor()
        cursor.execute(sql_query,(file_name,))
        file_history_data = cursor.fetchall()
        cursor.close()

        for data in file_history_data:
            file_history.append({'from':data[0],'to':data[1],'status':data[2]})
            # if data[0] not in file_history:
            #     file_history.append(data[0])
            # if data[1] not in file_history:
            #     file_history.append(data[1])

        month = transactions[0].strftime('%B')
        year = transactions[0].year

        key = f'{month}-{year}'

        if not history_requests.get(key):
            history_requests[key] = []
        history_requests[key].append({'id':transactions[5],'time':transactions[0],'from':transactions[1],'to':transactions[2],'letter':transactions[3],'description':transactions[4],'history':file_history}) 

    print(history_requests) 

    return render_template('history_copy.html', status= status, history_requests=history_requests, back=url_for('.history'), logout=url_for('.logout'))

@app.route('/message/<status>/<tranid>')
def message(status,tranid):
    return render_template('message.html', back=url_for('.display_history',status=status), logout=url_for('.logout'), tran={})

@app.route('/pending')
def pending():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    current_dept = session.get('username')
    pending_requests = {}

    #get all the pending requests
    sql_query =  '''SELECT tran_id,timestamp,from_dept,file_id,description
                    FROM transactions
                    WHERE to_dept = %s and status = 'pending'
                    ORDER BY timestamp DESC
        '''

    
    cursor = db.cursor()
    cursor.execute(sql_query,(current_dept,))
    pending_transactions_data = cursor.fetchall()
    cursor.close()
    
    for transactions in pending_transactions_data:
        month = transactions[1].strftime('%B')
        year = transactions[1].year

        key = f'{month}-{year}'

        if not pending_requests.get(key):
            pending_requests[key] = []
        pending_requests[key].append({'id':transactions[0],'time':transactions[1],'from':transactions[2],'letter':transactions[3],'description':transactions[4]})  


    return render_template('pending.html', pending_requests=pending_requests ,dept=dept, back=url_for('.dashboard'), logout=url_for('.logout'))

@app.route('/modify-transaction',methods=['POST'])
def modify_transaction():
    if not session.get('loggedin'):
        return redirect(url_for('login'))


    current_dept = session.get('username')

    action = request.form.get('action')
    id = request.form.get('id')
    current_dept = request.form.get('from_dept')
    
    file_name = request.form.get('file')
    description = request.form.get('description')

    present_time = datetime.datetime.now()

    if action == 'forward':
        to_dept = request.form.get('to_dept')
        sql_query = '''
                UPDATE transactions
                SET timestamp = %s,status = %s,to_dept = %s,from_dept = %s,description = %s
                WHERE tran_id = %s '''

        try:
            cursor = db.cursor()
            cursor.execute(sql_query,(present_time,'forwarded',to_dept,current_dept,description,id,))
            db.commit()
            cursor.close()
        except Exception as e:
            db.rollback()
            print("Error while updating transaction",e)
        else:
            flash('Successfully forwarded','success')

        dummy_query = '''INSERT 
                        INTO 
                        transactions 
                        (from_dept,to_dept,timestamp,file_id,status,description) values
                        (%s,%s,%s,%s,%s,%s)'''
        
        try:
            cursor = db.cursor()
            cursor.execute(dummy_query,(current_dept,to_dept,present_time,file_name,'pending',description,))
            db.commit()
            cursor.close()
        except Exception as e:
            db.rollback()
            print("Error while inserting dummy",e)
        else:
            print("success dummy")


    else:
        action = action+'ed'
        origin_dept = file_name[:file_name.find('_')]
        sql_query = '''
                UPDATE transactions
                SET timestamp = %s,status = %s,to_dept = %s,from_dept = %s,description = %s
                WHERE tran_id = %s '''

        try:
            cursor = db.cursor()
            cursor.execute(sql_query,(present_time,action,origin_dept,current_dept,description,id,))
            db.commit()
            cursor.close()
        except Exception as e:
            db.rollback()
            print("Error while accepting transaction",e)
        else:
            flash(f'Successfully {action}','success')
    return redirect(url_for('.pending'))

@app.route('/create-message',methods=['GET','POST'])
def create_message():
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    id = session.get('id')
    from_dept = session.get('username')

    if request.method == 'POST':
        to_dept = request.form.get('dept')
        file = request.files.get('letter')
        description = request.form.get('description')

        print("File",file)

        present_time = datetime.datetime.now()
        file_name = from_dept +'_'+ str(present_time.date())+str(present_time.time())

        file.save(os.getcwd()+'/files/'+file_name)
        print("Saved file as",file_name)

        #create a compose query
        sql_query = '''INSERT 
                        INTO 
                        transactions 
                        (from_dept,to_dept,timestamp,file_id,status,description) values
                        (%s,%s,%s,%s,%s,%s)
        '''

        try:
            cursor = db.cursor()
            cursor.execute(sql_query,(from_dept,to_dept,present_time,file_name,'composed',description,))
            db.commit()
            cursor.close()
        except Exception as e:
            db.rollback()
            print("Error while creating a letter",e)
        else:
            flash('Successfully placed the message','success')

        
        #create a dummy query

        sql_query = '''INSERT 
                        INTO 
                        transactions 
                        (from_dept,to_dept,timestamp,file_id,status,description) values
                        (%s,%s,%s,%s,%s,%s)
        '''

        try:
            cursor = db.cursor()
            cursor.execute(sql_query,(from_dept,to_dept,present_time,file_name,'pending',description,))
            db.commit()
            cursor.close()
        except Exception as e:
            db.rollback()
            print("Error while inserting dummy query")
        else:
            print('dummy successful')

        return redirect(url_for('dashboard'))

    return render_template('create_message.html',dept = dept, back=url_for('.dashboard'), logout=url_for('.logout'))


@app.route('/register')
def register():
    id = input("enter id")
    username = input("enter username")
    mailid=  input("mailid")
    password = input("password")
    password = generate_password_hash(password, method='sha256')
    print(id,username,mailid,password)
    sql_query = '''INSERT 
                        INTO 
                        departments 
                        (dept_id,dept_name,dept_email,password) values
                        (%s,%s,%s,%s)
        '''
    try:
        cursor = db.cursor()
        cursor.execute(sql_query,(id,username,mailid,password,))
        cursor.close()
        db.commit()
    except Exception as e:
        db.rollback()
        print("Error while inserting dummy query",e)
    else:
        print('dummy successful')
    return "did things in terminal"

@app.route('/file/<file_name>')
def get_file(file_name):

    file_path = os.getcwd() + '/files/'+file_name

    text = ''
    print(file_path)

    with open(file_path,'r') as file:
        text = file.read()
        print(text)
    
    return text

@app.route('/admin')
def admin_homepage():
    if session['admin']:
        return render_template('admin_homepage.html')

@app.route('/admin_file_history')
def admin_file_history():
    if session['admin']:
        return render_template('admin_homepage.html')

@app.route('/admin_add_user')
def admin_add_user():
    if session['admin']:
        return render_template('admin_homepage.html')

@app.route('/admin_modify_user')
def admin_modify_user():
    if session['admin']:
        return render_template('admin_homepage.html')
        
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
