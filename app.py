
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    role = db.Column(db.String(10))

class Sheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    filename = db.Column(db.String(100))
    uploaded_by = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100))
    filename = db.Column(db.String(100))
    sheet_id = db.Column(db.Integer)
    grade = db.Column(db.Integer)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100))
    status = db.Column(db.String(10))
    date = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def login_page():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    role = request.form['role']

    if role == "admin" and username == "mohamed hesham mohamed" and password == "asd7030":
        session['user'] = username
        session['role'] = 'admin'
        return redirect('/admin')

    user = User.query.filter_by(username=username, password=password, role=role).first()
    if user:
        session['user'] = username
        session['role'] = role
        return redirect(f'/{role}')
    return "بيانات الدخول غير صحيحة"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/admin')
def admin_page():
    if session.get('role') != 'admin':
        return redirect('/')
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    if session.get('role') != 'admin':
        return redirect('/')
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    role = request.form['role']
    if User.query.filter_by(username=username).first():
        return "المستخدم موجود بالفعل"
    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    return redirect('/admin')

@app.route('/delete_user', methods=['POST'])
def delete_user():
    if session.get('role') != 'admin':
        return redirect('/')
    username = request.form['username'].strip()
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect('/admin')

@app.route('/teacher')
def teacher_page():
    if session.get('role') != 'teacher':
        return redirect('/')
    answers = Answer.query.all()
    return render_template('teacher.html', answers=answers)

@app.route('/upload_sheet', methods=['POST'])
def upload_sheet():
    title = request.form['title']
    file = request.files['file']
    filename = file.filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    new_sheet = Sheet(title=title, filename=filename, uploaded_by=session['user'])
    db.session.add(new_sheet)
    db.session.commit()
    return redirect('/teacher')

@app.route('/grade_answer', methods=['POST'])
def grade_answer():
    if session.get('role') != 'teacher':
        return redirect('/')
    answer_id = request.form['answer_id']
    grade = request.form['grade']
    answer = Answer.query.get(answer_id)
    if answer:
        answer.grade = grade
        db.session.commit()
    return redirect('/teacher')

@app.route('/attendance_report')
def attendance_report():
    if session.get('role') != 'teacher':
        return redirect('/')
    students = db.session.query(
        Attendance.student_name,
        db.func.count(db.case((Attendance.status == "حاضر", 1))).label("present_count"),
        db.func.count(db.case((Attendance.status == "غائب", 1))).label("absent_count")
    ).group_by(Attendance.student_name).all()
    return render_template('attendance_report.html', students=students)

@app.route('/student')
def student_page():
    if session.get('role') != 'student':
        return redirect('/')
    sheets = Sheet.query.all()
    answers = Answer.query.filter_by(student_name=session['user']).all()
    return render_template('student.html', sheets=sheets, answers=answers)

@app.route('/upload_answer', methods=['POST'])
def upload_answer():
    student = session['user']
    file = request.files['file']
    sheet_id = request.form['sheet_id']
    filename = file.filename
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    answer = Answer(student_name=student, filename=filename, sheet_id=sheet_id)
    db.session.add(answer)
    db.session.commit()
    return redirect('/student')

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
