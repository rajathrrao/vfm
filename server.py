from flask import Flask, request, render_template, url_for, flash, session,redirect,jsonify, send_file, make_response
import sys,datetime,os,threading
from forms import LoginForm,RegisterForm,ModifyForm
from werkzeug.security import generate_password_hash, check_password_hash
import base64, shutil
from flask_mail import Mail, Message

#import blueprints
from user.routes import user

#import db configuration
from main import db,dept,app,mail
from file_utils import create_pdf, save_img

app.register_blueprint(user)

def send_mail(message_text,to_mail):
    message = Message(subject="Update on files",sender=mail_settings.get('MAIL_USERNAME'),
                        recipients=[to_mail],body=message_text)
    mail.send(message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form=LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            with db.cursor() as conn:
                conn.execute('SELECT * FROM departments WHERE dept_name = %s', (form.username.data,))
                user = conn.fetchone()
            if user:
                if check_password_hash(user[3], form.password.data):
                    session['loggedin'] = True
                    session['id'] = user[0]
                    session['username'] = user[1]
                    session['role'] = user[4]
                    flash("Login successful!!","success")
                    if user[4]==1:
                        return redirect(url_for('user/routes.dashboard'))
                    else:
                        return redirect(url_for('.admin_homepage'))
                else:
                    flash("Invalid username or password", "danger")
            else:
                flash("Invalid username or password", "danger")
    return render_template('loginpage.html', form=form,dept=dept) 

@app.route('/logout')
def logout():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/admin_homepage')
def admin_homepage():
    if not session.get('loggedin') or session.get('role')!=0:
        return redirect(url_for('login'))
    return render_template('admin_homepage.html',logout=url_for('.logout'))

@app.route('/admin_list_users')
def admin_list_users():
    if not session.get('loggedin') or session.get('role')!=0:
        return redirect(url_for('login'))
    sql_query =  '''SELECT dept_name,dept_email, dept_id, role
                    FROM departments
            '''

    cursor = db.cursor()
    cursor.execute(sql_query)
    departments_data = cursor.fetchall()
    cursor.close()

    dept_list = []

    for dept in departments_data:
        dept_list.append({'name':dept[0],'email':dept[1],'dept_id':dept[2],'dept_role':dept[3]})

    return render_template('admin_user_list.html',dept_list=dept_list,back=url_for('admin_homepage'),logout=url_for('.logout'))
        

@app.route('/admin_file_history')
def admin_file_history():
    if not session.get('loggedin') or session.get('role')!=0:
        return redirect(url_for('login'))

    sql_query =  '''SELECT timestamp,file_id,description,tran_id
                    FROM transactions
                    WHERE status = 'composed'
                    ORDER BY timestamp DESC
            '''

    cursor = db.cursor()
    cursor.execute(sql_query)
    pending_transactions_data = cursor.fetchall()
    cursor.close()

    files_list = []

    for file in pending_transactions_data:
        files_list.append({'file_name':file[1],'time':file[0],'comments':file[2],'tran_id':file[3]})

    return render_template('admin_list.html',files_list=files_list,back=url_for('admin_homepage'),logout=url_for('.logout'),status='composed')

@app.route('/admin_add_user',methods=['GET','POST'])
def admin_add_user():
    if not session.get('loggedin') or session.get('role')!=0:
        return redirect(url_for('login'))

    form=RegisterForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            username = form.username.data
            email = form.email.data
            role = form.role.data
            password = form.password.data

            password_hash = generate_password_hash(password, method='sha256')

            sql_query = '''INSERT 
                        INTO 
                        departments 
                        (dept_name,dept_email,password,role) values
                        (%s,%s,%s,%s)
                    '''
            try:
                cursor = db.cursor()
                cursor.execute(sql_query,(username,email,password_hash,role))
                cursor.close()
                db.commit()

                cursor = db.cursor()
                cursor.execute('SELECT dept_id from departments where dept_name=%s',(username))
                dept_id = cursor.fetchone()
                cursor.close()

            except Exception as e:
                db.rollback()
                print("Error while inserting new user",e)
            else:
                flash(f'Added user {username}.','success')

            if role=='1':
                dept.append([dept_id[0], username, email])
  
            return redirect(url_for('admin_list_users'))

    return render_template('admin_add_user.html',form=form, logout=url_for('logout'), back=url_for('admin_list_users'))

@app.route('/admin_modify_user/<username>',methods=['GET','POST'])
def admin_modify_user(username):
    if not session.get('loggedin') or session.get('role')!=0:
        return redirect(url_for('login'))

    form=ModifyForm()    

    if request.method == 'POST':
            #insert
        email = form.email.data
        password = form.password.data

        if password!='':
            password_hash = generate_password_hash(password,method='sha256')

            sql_query = '''UPDATE  
                        departments SET 
                        dept_email = %s, password = %s 
                        where dept_name = %s
                    '''
            try:
                cursor = db.cursor()
                cursor.execute(sql_query,(email,password_hash,username,))
                cursor.close()
                db.commit()
            except Exception as e:
                db.rollback()
                print("Error while modifying user",e)
            else:
                flash(f'Modified user {username}.','success')

        else:

            sql_query = '''UPDATE  
                        departments SET 
                        dept_email = %s
                        where dept_name = %s
                    '''
            try:
                cursor = db.cursor()
                cursor.execute(sql_query,(email,username,))
                cursor.close()
                db.commit()
            except Exception as e:
                db.rollback()
                print("Error while modifying user",e)
            else:
                flash(f'Modified user {username}.','success')


        for dep in dept:
            if dep[1] == username:
                dep[2] = email

        return redirect(url_for('admin_list_users'))

              
    cursor = db.cursor()
    cursor.execute('SELECT dept_id,dept_name,dept_email FROM departments where dept_name = %s',(username,))
    departments_data = cursor.fetchone()
    cursor.close()
    form.username.data = username
    form.email.data = departments_data[2]
        
    return render_template('admin_modify_user.html',form=form, logout=url_for('logout'), back=url_for('admin_list_users'))

@app.route('/delete/<file_id>')
def delete_file(file_id):
    if not session.get('loggedin') or session.get('role')!=0:
        return redirect(url_for('login'))
    try:
        os.remove(os.getcwd()+'/files/original/'+file_id+'.pdf')
        os.remove(os.getcwd()+'/static/files/'+file_id+'.pdf')
        os.remove(os.getcwd()+'/static/files/'+file_id+'.tex')
        shutil.rmtree(os.getcwd()+'/files/images/'+file_id)

        sql_query = '''DELETE FROM transactions WHERE file_id=%s'''

        cursor = db.cursor()
        cursor.execute(sql_query,(file_id,))
        cursor.close()
        db.commit()

        flash("Deleted file with File ID "+file_id,"success")
    except Exception as e:
        db.rollback()
        print("Error while deleting transactions",e)
        flash("Deletion unsuccessful","danger")
    except:
        flash("Deletion unsuccessful","danger")
    return redirect(url_for('admin_file_history'))

@app.route('/delete_user/<dept_id>')
def delete_user(dept_id):
    if not session.get('loggedin') or session.get('role')!=0:
        return redirect(url_for('login'))
    try:
        sql_query = '''DELETE FROM departments WHERE dept_id=%s'''

        cursor = db.cursor()
        cursor.execute(sql_query,(dept_id,))
        cursor.close()
        db.commit()
        
        for ele in dept:
            if str(ele[0]) == dept_id:
                dept.remove(ele)
    
    except Exception as e:
        db.rollback()
        print("Error while deleting departments",e)
        flash("Deletion unsuccessful","danger")
    return redirect(url_for('admin_list_users'))

@app.route('/download/<file_name>')
def download(file_name):
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    
    
    file_path=os.getcwd()+'/static/files/'+file_name+'.pdf'
    return send_file(file_path, as_attachment = True,attachment_filename=file_name+'.pdf', cache_timeout=0)

@app.route('/preview/<file_name>',methods=['POST'])
def preview(file_name):
    if not session.get('loggedin') or session.get('role')!=1:
        return redirect(url_for('login'))
    from_dept = session.get('username')
    file_id = request.form.get('file_id')
    to_dept = request.form.get('dept')
    file = request.files.get('letter')
    description = request.form.get('description')
    comment = request.form.get('comment')
    digital_sign = request.files.get('digital_sign')

    sql_query = '''SELECT EXISTS(SELECT 1 FROM transactions WHERE file_id=%s)'''
    try:
        cursor = db.cursor()
        cursor.execute(sql_query,(file_id,))
        exists = cursor.fetchone()
        cursor.close()
        if exists[0]==1:
            return "File ID already exists"
    except:
        print("select from table did not work")

    present_time = datetime.datetime.now()

    file_path = os.getcwd()+'/static/files/'+file_id
    original_file = os.getcwd()+'/files/original/'+file_id+'.pdf'
    img_name = "".join(from_dept.split())+str(present_time.date())+str(present_time.time())
    sign_path = os.getcwd()+'/files/images/'+file_id+'/'+img_name

    save_img(digital_sign, 'files/images/'+file_id, img_name)
    if not os.path.exists('files/original'):
        os.makedirs('files/original')
    file.save(original_file)
    if not os.path.exists('static/files'):
        os.makedirs('static/files')
    create_pdf(file_path, original_file, from_dept, comment, sign_path+'.jpeg', "composed")

    new_filename = url_for('static',filename='files/'+file_name+'.pdf')

    try:
        encoded_string=''
        with open(os.getcwd()+'/'+new_filename, "rb") as pdf_file:
            encoded_string = base64.b64encode(pdf_file.read())
        os.remove(file_path+'.pdf')
        os.remove(file_path+'.tex')
        os.remove(sign_path+'.jpeg')
        os.remove(original_file)
    except:
        print("os related error")
    return encoded_string

@app.route('/view/<file_name>')
def view(file_name):
    if not session.get('loggedin'):
        return redirect(url_for('login'))

    new_filename = url_for('static',filename='files/'+file_name+'.pdf')
    return send_file(os.getcwd()+'/'+new_filename, as_attachment=False, cache_timeout=0)

    
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
