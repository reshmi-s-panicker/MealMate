from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import os
import calendar
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = secrets.token_hex(16)

db = SQLAlchemy(app)

# Define Models
class Admin(db.Model):
    __tablename__ = 'admin'
    AdminID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.Password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.Password, password)

class Student(db.Model):
    __tablename__ = 'student'
    StudentID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    Password = db.Column(db.String(200), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    guardianName = db.Column(db.String(100), nullable=False)
    guardianMobile = db.Column(db.String(20), nullable=False)
    RoomNo = db.Column(db.String(10), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    registration_no = db.Column(db.String(20), unique=True, nullable=False)
    PaidAmount = db.Column(db.Float, default=0.0)

    def set_password(self, password):
        self.Password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.Password, password)

class WeeklyMenu(db.Model):
    __tablename__ = 'weeklymenu'
    MenuID = db.Column(db.Integer, primary_key=True)
    Date = db.Column(db.Date, nullable=False)
    Breakfast = db.Column(db.String(255))
    Lunch = db.Column(db.String(255))
    Dinner = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<WeeklyMenu {self.Date}>'

class MealSelection(db.Model):
    __tablename__ = 'meal_selection'
    SelectionID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.Integer, db.ForeignKey('student.StudentID'), nullable=False)
    Date = db.Column(db.Date, nullable=False)
    Breakfast = db.Column(db.String(3), default='No')
    Lunch = db.Column(db.String(3), default='No')
    Dinner = db.Column(db.String(3), default='No')
    student = db.relationship('Student', backref='meal_selections')

class Feedback(db.Model):
    __tablename__ = 'feedback'
    FeedbackID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.Integer, db.ForeignKey('student.StudentID'), nullable=False)
    Comments = db.Column(db.Text, nullable=False)
    Rating = db.Column(db.Integer)
    Category = db.Column(db.String(50))
    FeedbackDate = db.Column(db.Date, default=date.today)
    student = db.relationship('Student', backref='feedbacks')

class Payment(db.Model):
    __tablename__ = 'payment'
    PaymentID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.Integer, db.ForeignKey('student.StudentID'), nullable=False)
    TransactionID = db.Column(db.String(100), nullable=False)
    PaymentMethod = db.Column(db.String(50), nullable=False)
    PaymentDate = db.Column(db.Date, nullable=False)
    Amount = db.Column(db.Float, nullable=False)
    Status = db.Column(db.String(20), default='Pending')  # Pending, Verified, Rejected
    PaymentProof = db.Column(db.String(255))  # Path to stored image
    student = db.relationship('Student', backref='payments')

# Create tables
def create_tables():
    with app.app_context():
        db.create_all()

# Initialize Database
def init_db():
    with app.app_context():
        # Drop all tables if they exist
        db.drop_all()
        # Create all tables
        db.create_all()
        
        # Create default admin
        admin = Admin(Name='Sania', Email='sania@admin.com')
        admin.set_password('sania123')
        db.session.add(admin)
        
        # Create default student with all required fields
        student = Student(
            Name='Test Student',
            Email='student@example.com',
            mobile='1234567890',
            guardianName='Parent Name',
            guardianMobile='9876543210',
            RoomNo='101',
            year='1st Year',
            branch='CSE',
            registration_no='2024001'
        )
        student.set_password('student123')
        db.session.add(student)
        
        # Create sample menu for the whole week
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        
        for i in range(7):
            current_date = start_of_week + timedelta(days=i)
            menu = WeeklyMenu(
                Date=current_date,
                Breakfast='Sample Breakfast Menu',
                Lunch='Sample Lunch Menu',
                Dinner='Sample Dinner Menu'
            )
            db.session.add(menu)
        
        # Commit the changes
        db.session.commit()
        print("Database initialized successfully!")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin = Admin.query.filter_by(Email=email).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.AdminID
            session['admin_name'] = admin.Name
            flash('Login successful!', 'success')
            return redirect(url_for('alogin'))
        else:
            flash('Invalid email or password', 'error')
            return render_template('admin.html')
    return render_template('admin.html')

@app.route('/alogin')
def alogin():
    if 'admin_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('admin'))
    
    admin = Admin.query.get(session['admin_id'])
    if not admin:
        session.clear()
        flash('Admin not found', 'error')
        return redirect(url_for('admin'))
    
    # Get all students for counting
    students = Student.query.all()
    student_count = len(students)
    
    # Get recent students (added in the last 7 days)
    recent_students = Student.query.filter(
        Student.StudentID > (Student.query.count() - 5)  # Get last 5 students
    ).all()
    
    return render_template('alogin.html', 
                         admin=admin, 
                         students=students,
                         student_count=student_count,
                         recent_students=recent_students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'admin_id' not in session:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        try:
            # Get all form data with correct field names
            name = request.form.get('Name')
            email = request.form.get('Email')
            password = request.form.get('Password')
            mobile = request.form.get('mobile')
            guardian_name = request.form.get('guardianName')
            guardian_mobile = request.form.get('guardianMobile')
            room_no = request.form.get('RoomNo')
            year = request.form.get('year')
            branch = request.form.get('branch')
            registration_no = request.form.get('registration_no')
            
            # Validate required fields
            if not all([name, email, password, mobile, guardian_name, guardian_mobile, room_no, year, branch, registration_no]):
                flash('All fields are required', 'error')
                return redirect(url_for('add_student'))
            
            # Check if email or registration number already exists
            if Student.query.filter_by(Email=email).first():
                flash('Email already registered', 'error')
                return redirect(url_for('add_student'))
            
            if Student.query.filter_by(registration_no=registration_no).first():
                flash('Registration number already exists', 'error')
                return redirect(url_for('add_student'))
            
            # Create new student with all details
            new_student = Student(
                Name=name,
                Email=email,
                mobile=mobile,
                guardianName=guardian_name,
                guardianMobile=guardian_mobile,
                RoomNo=room_no,
                year=year,
                branch=branch,
                registration_no=registration_no
            )
            new_student.set_password(password)
            
            db.session.add(new_student)
            db.session.commit()
            
            flash('Student added successfully!', 'success')
            return redirect(url_for('alogin'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding student: {str(e)}")  # Debug print
            flash(f'Error adding student: {str(e)}', 'error')
            return redirect(url_for('add_student'))
    
    return render_template('add-new.html')

@app.route('/search_student', methods=['GET', 'POST'])
def search_student():
    if 'admin_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        students = Student.query.filter(
            (Student.Name.ilike(f'%{search_term}%')) |
            (Student.Email.ilike(f'%{search_term}%')) |
            (Student.RoomNo.ilike(f'%{search_term}%'))
        ).all()
    else:
        students = []
        search_term = ''
    
    return render_template('search_student.html', students=students, search_term=search_term)

@app.route('/view_students', methods=['GET', 'POST'])
def view_students():
    if 'admin_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        if search_term:
            students = Student.query.filter(Student.registration_no.ilike(f'%{search_term}%')).all()
        else:
            students = Student.query.all()
    else:
        students = Student.query.all()
        search_term = ''
    
    return render_template('view_students.html', students=students, search_term=search_term)

@app.route('/manage-menu', methods=['GET', 'POST'])
def manage_menu():
    if 'admin_id' not in session:
        return redirect(url_for('admin'))
    
    # Get current date and calculate week range
    current_date = datetime.now().date()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get weekly menu
    weekly_menu = WeeklyMenu.query.filter(
        WeeklyMenu.Date >= start_of_week,
        WeeklyMenu.Date <= end_of_week
    ).order_by(WeeklyMenu.Date).all()
    
    # Create menu entries for missing days
    menu_by_date = {menu.Date: menu for menu in weekly_menu}
    menu_list = []
    current_date_iter = start_of_week
    while current_date_iter <= end_of_week:
        menu = menu_by_date.get(current_date_iter)
        if not menu:
            menu = WeeklyMenu(
                Date=current_date_iter,
                Breakfast='',
                Lunch='',
                Dinner=''
            )
            db.session.add(menu)
        menu_list.append(menu)
        current_date_iter += timedelta(days=1)
    
    # Handle POST request for menu updates
    if request.method == 'POST':
        try:
            # Process menu updates
            for key, value in request.form.items():
                if '_' not in key:
                    continue
                
                meal_type, date_str = key.split('_')
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Get or create menu for this date
                menu = WeeklyMenu.query.filter_by(Date=date).first()
                if not menu:
                    menu = WeeklyMenu(Date=date)
                    db.session.add(menu)
                
                # Update menu items
                if meal_type == 'breakfast':
                    menu.Breakfast = value
                elif meal_type == 'lunch':
                    menu.Lunch = value
                elif meal_type == 'dinner':
                    menu.Dinner = value
            
            db.session.commit()
            flash('Menu updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating menu: {str(e)}', 'error')
        
        return redirect(url_for('manage_menu'))
    
    # Get the requested month (default to current month)
    requested_month = request.args.get('month', '').lower()
    
    # Map month names to numbers for 2025
    month_mapping = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    # Get the month number from the mapping, default to current month
    current_month = month_mapping.get(requested_month, current_date.month)
    year = 2025
    
    # Get the first and last day of the selected month
    first_day = datetime(year, current_month, 1).date()
    if current_month == 12:
        last_day = datetime(year, 12, 31).date()
    else:
        last_day = datetime(year, current_month + 1, 1).date() - timedelta(days=1)
    
    # Get monthly menu data
    monthly_menu = WeeklyMenu.query.filter(
        WeeklyMenu.Date >= first_day,
        WeeklyMenu.Date <= last_day
    ).order_by(WeeklyMenu.Date).all()
    
    # Create menu entries for missing days in the month
    monthly_dates = {menu.Date for menu in monthly_menu}
    current_date = first_day
    while current_date <= last_day:
        if current_date not in monthly_dates:
            menu = WeeklyMenu(
                Date=current_date,
                Breakfast='',
                Lunch='',
                Dinner=''
            )
            db.session.add(menu)
            monthly_menu.append(menu)
        current_date += timedelta(days=1)
    
    # Sort monthly menu by date
    monthly_menu.sort(key=lambda x: x.Date)
    
    # Initialize meal selections dictionary
    meal_selections = {}
    
    # For each day in the month, get meal selections
    current_date = first_day
    while current_date <= last_day:
        date_str = current_date.strftime('%Y-%m-%d')
        meal_selections[date_str] = {
            'breakfast': {'count': '0', 'students': []},
            'lunch': {'count': '0', 'students': []},
            'dinner': {'count': '0', 'students': []}
        }
        
        # Get selections for this date
        selections = MealSelection.query.filter(
            MealSelection.Date == current_date
        ).all()
        
        # Process each selection
        for selection in selections:
            student_info = {
                'name': selection.student.Name if selection.student else 'Unknown',
                'regno': selection.student.registration_no if selection.student else 'N/A'
            }
            
            if selection.Breakfast == 'Yes':
                meal_selections[date_str]['breakfast']['count'] = '1'
                meal_selections[date_str]['breakfast']['students'].append(student_info)
            if selection.Lunch == 'Yes':
                meal_selections[date_str]['lunch']['count'] = '1'
                meal_selections[date_str]['lunch']['students'].append(student_info)
            if selection.Dinner == 'Yes':
                meal_selections[date_str]['dinner']['count'] = '1'
                meal_selections[date_str]['dinner']['students'].append(student_info)
        
        current_date += timedelta(days=1)
    
    # Convert weekly menu to serializable format
    weekly_menu_data = []
    for menu in menu_list:
        weekly_menu_data.append({
            'date': menu.Date.strftime('%Y-%m-%d'),
            'breakfast': menu.Breakfast or '',
            'lunch': menu.Lunch or '',
            'dinner': menu.Dinner or ''
        })
    
    # Convert monthly menu to serializable format
    monthly_menu_data = []
    for menu in monthly_menu:
        monthly_menu_data.append({
            'date': menu.Date.strftime('%Y-%m-%d'),
            'breakfast': menu.Breakfast or '',
            'lunch': menu.Lunch or '',
            'dinner': menu.Dinner or ''
        })
    
    return render_template('manage-menu.html', 
                         weekly_menu=weekly_menu_data,
                         monthly_menu=monthly_menu_data,
                         meal_selections=meal_selections,
                         current_month=current_month)

@app.route('/view_feedback')
def view_feedback():
    if 'admin_id' not in session:
        return redirect(url_for('admin'))
    
    # Get all feedback with student information
    feedbacks = db.session.query(
        Feedback, Student
    ).join(
        Student, Feedback.StudentID == Student.StudentID
    ).order_by(
        Feedback.FeedbackDate.desc()
    ).all()
    
    return render_template('a_feedback.html', feedbacks=feedbacks)

@app.route('/a_feedback')
def a_feedback():
    if 'admin_id' not in session:
        return redirect(url_for('admin'))
    
    feedbacks = db.session.query(Feedback, Student).join(Student).order_by(Feedback.FeedbackDate.desc()).all()
    return render_template('a_feedback.html', feedbacks=feedbacks)

@app.route('/view_fee_details')
def view_fee_details():
    if 'admin_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('admin'))
    
    # Get all pending payments
    pending_payments = Payment.query.filter_by(Status='Pending').order_by(Payment.PaymentDate.desc()).all()
    
    # Get all students with their payment history
    students = Student.query.all()
    
    # Get the selected month from query parameters
    selected_month = request.args.get('month', 'current')
    
    # Calculate mess bill for each student based on meal selections
    for student in students:
        if selected_month == 'current':
            # Get the current week's date range
            current_date = datetime.now().date()
            start_of_week = current_date - timedelta(days=current_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            # Get meal selections for the current week
            meal_selections = MealSelection.query.filter(
                MealSelection.StudentID == student.StudentID,
                MealSelection.Date >= start_of_week,
                MealSelection.Date <= end_of_week
            ).all()
        else:
            # Convert month name to number (1-12)
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            month_num = month_map.get(selected_month.lower(), 1)
            
            # Get the first and last day of the selected month
            current_year = datetime.now().year
            start_of_month = datetime(current_year, month_num, 1).date()
            if month_num == 12:
                end_of_month = datetime(current_year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_of_month = datetime(current_year, month_num + 1, 1).date() - timedelta(days=1)
            
            # Get meal selections for the selected month
            meal_selections = MealSelection.query.filter(
                MealSelection.StudentID == student.StudentID,
                MealSelection.Date >= start_of_month,
                MealSelection.Date <= end_of_month
            ).all()
        
        # Count unique dates where any meal was selected
        dates_with_meals = set()
        for selection in meal_selections:
            if selection.Breakfast == 'Yes' or selection.Lunch == 'Yes' or selection.Dinner == 'Yes':
                dates_with_meals.add(selection.Date)
        
        # Calculate mess bill (₹100 per day with any meal)
        student.mess_bill = len(dates_with_meals) * 100
    
    return render_template('view_fee_details.html', 
                         students=students, 
                         pending_payments=pending_payments,
                         selected_month=selected_month)

@app.route('/manage_weekly_menu')
def manage_weekly_menu():
    if 'admin_id' not in session:
        return redirect(url_for('admin'))
    
    # Get current week's menu
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    weekly_menu = WeeklyMenu.query.filter(
        WeeklyMenu.Date >= week_start,
        WeeklyMenu.Date <= week_end
    ).order_by(WeeklyMenu.Date).all()
    
    # Get the requested month (default to current month)
    requested_month = request.args.get('month', '').lower()
    
    # Map month names to numbers for 2025
    month_mapping = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    # Get the month number from the mapping, default to current month
    current_month = month_mapping.get(requested_month, today.month)
    year = 2025
    
    # Get the first and last day of the selected month
    first_day = datetime(year, current_month, 1).date()
    if current_month == 12:
        last_day = datetime(year, 12, 31).date()
    else:
        last_day = datetime(year, current_month + 1, 1).date() - timedelta(days=1)
    
    # Get monthly menu data
    monthly_menu = WeeklyMenu.query.filter(
        WeeklyMenu.Date >= first_day,
        WeeklyMenu.Date <= last_day
    ).order_by(WeeklyMenu.Date).all()
    
    # Create menu entries for missing days in the month
    monthly_dates = {menu.Date for menu in monthly_menu}
    current_date = first_day
    while current_date <= last_day:
        if current_date not in monthly_dates:
            menu = WeeklyMenu(
                Date=current_date,
                Breakfast='',
                Lunch='',
                Dinner=''
            )
            db.session.add(menu)
            monthly_menu.append(menu)
        current_date += timedelta(days=1)
    
    # Sort monthly menu by date
    monthly_menu.sort(key=lambda x: x.Date)
    
    # Initialize meal selections dictionary
    meal_selections = {}
    
    # For each day in the month, get meal selections
    current_date = first_day
    while current_date <= last_day:
        date_str = current_date.strftime('%Y-%m-%d')
        meal_selections[date_str] = {
            'breakfast': {'count': '0', 'students': []},
            'lunch': {'count': '0', 'students': []},
            'dinner': {'count': '0', 'students': []}
        }
        
        # Get selections for this date
        selections = MealSelection.query.filter(
            MealSelection.Date == current_date
        ).all()
        
        # Process each selection
        for selection in selections:
            student_info = {
                'name': selection.student.Name if selection.student else 'Unknown',
                'regno': selection.student.registration_no if selection.student else 'N/A'
            }
            
            if selection.Breakfast == 'Yes':
                meal_selections[date_str]['breakfast']['count'] = '1'
                meal_selections[date_str]['breakfast']['students'].append(student_info)
            if selection.Lunch == 'Yes':
                meal_selections[date_str]['lunch']['count'] = '1'
                meal_selections[date_str]['lunch']['students'].append(student_info)
            if selection.Dinner == 'Yes':
                meal_selections[date_str]['dinner']['count'] = '1'
                meal_selections[date_str]['dinner']['students'].append(student_info)
        
        current_date += timedelta(days=1)
    
    # Convert weekly menu to serializable format
    weekly_menu_data = []
    for menu in weekly_menu:
        weekly_menu_data.append({
            'date': menu.Date.strftime('%Y-%m-%d'),
            'breakfast': menu.Breakfast or '',
            'lunch': menu.Lunch or '',
            'dinner': menu.Dinner or ''
        })
    
    # Convert monthly menu to serializable format
    monthly_menu_data = []
    for menu in monthly_menu:
        monthly_menu_data.append({
            'date': menu.Date.strftime('%Y-%m-%d'),
            'breakfast': menu.Breakfast or '',
            'lunch': menu.Lunch or '',
            'dinner': menu.Dinner or ''
        })
    
    return render_template('manage-menu.html', 
                         weekly_menu=weekly_menu_data,
                         monthly_menu=monthly_menu_data,
                         meal_selections=meal_selections,
                         current_month=current_month)

@app.route('/student', methods=['GET', 'POST'])
def student():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        student = Student.query.filter_by(Email=email).first()
        if student and student.check_password(password):
            session['student_id'] = student.StudentID
            session['student_name'] = student.Name
            flash('Login successful!', 'success')
            return redirect(url_for('slogin'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('student.html')

@app.route('/slogin', methods=['GET', 'POST'])
def slogin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        student = Student.query.filter_by(Email=email).first()
        
        if student and student.check_password(password):
            session['student_id'] = student.StudentID
            flash('Login successful!', 'success')
            return redirect(url_for('slogin'))
        else:
            flash('Invalid email or password', 'error')
            return redirect(url_for('student'))
    
    if 'student_id' in session:
        student = Student.query.get(session['student_id'])
        if student:
            # Get the current week's menu
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            weekly_menu = WeeklyMenu.query.filter(
                WeeklyMenu.Date >= start_of_week,
                WeeklyMenu.Date <= end_of_week
            ).order_by(WeeklyMenu.Date).all()
            
            # Get student's meal selections for the week
            meal_selections = MealSelection.query.filter(
                MealSelection.StudentID == student.StudentID,
                MealSelection.Date >= start_of_week,
                MealSelection.Date <= end_of_week
            ).order_by(MealSelection.Date).all()
            
            return render_template('slogin.html', 
                                 student=student, 
                                 weekly_menu=weekly_menu,
                                 meal_selections=meal_selections)
    
    return redirect(url_for('student'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'student_id' not in session:
        return redirect(url_for('student'))
    
    if request.method == 'POST':
        try:
            student_id = session['student_id']
            comments = request.form.get('comments')
            rating = request.form.get('rating')
            categories = request.form.get('categories', '').split(',')
            categories = [cat.strip() for cat in categories if cat.strip()]
            
            if not comments:
                flash('Please provide feedback comments', 'error')
                return redirect(url_for('feedback'))
            
            # Create new feedback entry
            new_feedback = Feedback(
                StudentID=student_id,
                Comments=comments,
                Rating=rating,
                Category=', '.join(categories) if categories else None,
                FeedbackDate=date.today()
            )
            
            db.session.add(new_feedback)
            db.session.commit()
            
            flash('Thank you for your feedback!', 'success')
            return redirect(url_for('slogin'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting feedback: {str(e)}', 'error')
            return redirect(url_for('feedback'))
    
    return render_template('feedback.html')

@app.route('/view_dues')
def view_dues():
    if 'admin_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('admin'))
    
    admin = Admin.query.get(session['admin_id'])
    if not admin:
        session.clear()
        flash('Admin not found', 'error')
        return redirect(url_for('admin'))
    
    # Get all students with their meal selections
    students = Student.query.all()
    
    # Get the selected month from query parameters
    selected_month = request.args.get('month', 'current')
    
    # Calculate mess bill for each student based on meal selections
    for student in students:
        if selected_month == 'current':
            # Get the current week's date range
            current_date = datetime.now().date()
            start_of_week = current_date - timedelta(days=current_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            # Get meal selections for the current week
            meal_selections = MealSelection.query.filter(
                MealSelection.StudentID == student.StudentID,
                MealSelection.Date >= start_of_week,
                MealSelection.Date <= end_of_week
            ).all()
        else:
            # Convert month name to number (1-12)
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            month_num = month_map.get(selected_month.lower(), 1)
            
            # Get the first and last day of the selected month
            current_year = datetime.now().year
            start_of_month = datetime(current_year, month_num, 1).date()
            if month_num == 12:
                end_of_month = datetime(current_year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_of_month = datetime(current_year, month_num + 1, 1).date() - timedelta(days=1)
            
            # Get meal selections for the selected month
            meal_selections = MealSelection.query.filter(
                MealSelection.StudentID == student.StudentID,
                MealSelection.Date >= start_of_month,
                MealSelection.Date <= end_of_month
            ).all()
        
        # Count unique dates where any meal was selected
        dates_with_meals = set()
        for selection in meal_selections:
            if selection.Breakfast == 'Yes' or selection.Lunch == 'Yes' or selection.Dinner == 'Yes':
                dates_with_meals.add(selection.Date)
        
        # Calculate mess bill (₹100 per day with any meal)
        student.mess_bill = len(dates_with_meals) * 100
        
        # Calculate total fee and balance
        student.total_fee = 2300 + student.mess_bill  # Room rent + Mess bill
        student.balance = student.total_fee - (student.PaidAmount or 0)
    
    return render_template('view_dues.html', students=students, selected_month=selected_month)

@app.route('/menu')
def menu():
    if 'student_id' not in session:
        return redirect(url_for('student'))
    
    student = Student.query.get(session['student_id'])
    if not student:
        session.clear()
        return redirect(url_for('student'))
    
    # Get current date and calculate week range
    current_date = datetime.now().date()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get weekly menu
    weekly_menu = WeeklyMenu.query.filter(
        WeeklyMenu.Date >= start_of_week,
        WeeklyMenu.Date <= end_of_week
    ).order_by(WeeklyMenu.Date).all()
    
    # Create menu entries for missing days
    menu_by_date = {menu.Date: menu for menu in weekly_menu}
    menu_list = []
    current_date_iter = start_of_week
    while current_date_iter <= end_of_week:
        menu = menu_by_date.get(current_date_iter)
        if not menu:
            menu = WeeklyMenu(
                Date=current_date_iter,
                Breakfast='',
                Lunch='',
                Dinner=''
            )
            db.session.add(menu)
        menu_list.append(menu)
        current_date_iter += timedelta(days=1)
    
    # Get student's meal selections for the week
    selections = MealSelection.query.filter(
        MealSelection.StudentID == student.StudentID,
        MealSelection.Date >= start_of_week,
        MealSelection.Date <= end_of_week
    ).all()
    
    # Convert selections to dictionary for easy lookup
    selections_by_date = {selection.Date: selection for selection in selections}
    
    # Get the requested month (default to current month)
    requested_month = request.args.get('month', '').lower()
    
    # Map month names to numbers for 2025
    month_mapping = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    # Get the month number from the mapping, default to current month
    current_month = month_mapping.get(requested_month, current_date.month)
    year = 2025
    
    # Get the first and last day of the selected month
    first_day = datetime(year, current_month, 1).date()
    if current_month == 12:
        last_day = datetime(year, 12, 31).date()
    else:
        last_day = datetime(year, current_month + 1, 1).date() - timedelta(days=1)
    
    # Get monthly menu data
    monthly_menu = WeeklyMenu.query.filter(
        WeeklyMenu.Date >= first_day,
        WeeklyMenu.Date <= last_day
    ).order_by(WeeklyMenu.Date).all()
    
    # Create menu entries for missing days in the month
    monthly_dates = {menu.Date for menu in monthly_menu}
    current_date = first_day
    while current_date <= last_day:
        if current_date not in monthly_dates:
            menu = WeeklyMenu(
                Date=current_date,
                Breakfast='',
                Lunch='',
                Dinner=''
            )
            db.session.add(menu)
            monthly_menu.append(menu)
        current_date += timedelta(days=1)
    
    # Sort monthly menu by date
    monthly_menu.sort(key=lambda x: x.Date)
    
    # Convert weekly menu to serializable format
    weekly_menu_data = []
    for menu in menu_list:
        weekly_menu_data.append({
            'date': menu.Date.strftime('%Y-%m-%d'),
            'breakfast': menu.Breakfast or '',
            'lunch': menu.Lunch or '',
            'dinner': menu.Dinner or ''
        })
    
    # Convert monthly menu to serializable format
    monthly_menu_data = []
    for menu in monthly_menu:
        monthly_menu_data.append({
            'date': menu.Date.strftime('%Y-%m-%d'),
            'breakfast': menu.Breakfast or '',
            'lunch': menu.Lunch or '',
            'dinner': menu.Dinner or ''
        })
    
    # Convert selections to serializable format
    selections_data = []
    for selection in selections:
        selections_data.append({
            'date': selection.Date.strftime('%Y-%m-%d'),
            'breakfast': selection.Breakfast,
            'lunch': selection.Lunch,
            'dinner': selection.Dinner
        })
    
    return render_template('menu.html',
                         student=student,
                         weekly_menu=weekly_menu_data,
                         monthly_menu=monthly_menu_data,
                         selections=selections_data,
                         current_month=current_month)

@app.route('/select_meals', methods=['POST'])
def select_meals():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    try:
        data = request.get_json()
        date = data.get('date')
        meal_type = data.get('mealType')
        is_selected = data.get('isSelected')  # This will be true or false

        # Convert date string to datetime
        meal_date = datetime.strptime(date, '%Y-%m-%d').date()

        # Get existing selection or create new one
        selection = MealSelection.query.filter_by(
            StudentID=session['student_id'],
            Date=meal_date
        ).first()

        if not selection:
            selection = MealSelection(
                StudentID=session['student_id'],
                Date=meal_date,
                Breakfast='No',
                Lunch='No',
                Dinner='No'
            )
            db.session.add(selection)

        # Update the appropriate meal type
        if meal_type == 'breakfast':
            selection.Breakfast = 'Yes' if is_selected else 'No'
        elif meal_type == 'lunch':
            selection.Lunch = 'Yes' if is_selected else 'No'
        elif meal_type == 'dinner':
            selection.Dinner = 'Yes' if is_selected else 'No'

        db.session.commit()
        return jsonify({'success': True, 'message': 'Selection updated successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/details', methods=['GET', 'POST'])
def details():
    if 'admin_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('admin'))
    
    try:
        if request.method == 'POST':
            search_term = request.form.get('search_term', '')
            if search_term:
                students = Student.query.filter(
                    (Student.registration_no.ilike(f'%{search_term}%')) |
                    (Student.Name.ilike(f'%{search_term}%')) |
                    (Student.Email.ilike(f'%{search_term}%')) |
                    (Student.RoomNo.ilike(f'%{search_term}%'))
                ).all()
            else:
                students = Student.query.all()
        else:
            students = Student.query.all()
            search_term = ''
        
        # Convert students to a list of dictionaries for easier template rendering
        students_data = []
        for student in students:
            students_data.append({
                'StudentID': student.StudentID,
                'Name': student.Name,
                'Email': student.Email,
                'mobile': student.mobile,
                'guardianName': student.guardianName,
                'guardianMobile': student.guardianMobile,
                'RoomNo': student.RoomNo,
                'year': student.year,
                'branch': student.branch,
                'registration_no': student.registration_no
            })
            
        return render_template('details.html', 
                             students=students_data, 
                             search_term=search_term)
    except Exception as e:
        print(f"Error fetching students: {str(e)}")  # Debug print
        flash('Error fetching student details', 'error')
        return redirect(url_for('alogin'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin'))
    
    try:
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('alogin'))

@app.route('/dues')
def dues():
    if 'student_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('student'))
    
    student = Student.query.get(session['student_id'])
    if not student:
        session.clear()
        flash('Student not found', 'error')
        return redirect(url_for('student'))
    
    # Get the current week's date range
    current_date = datetime.now().date()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # Get meal selections for the current week
    meal_selections = MealSelection.query.filter(
        MealSelection.StudentID == student.StudentID,
        MealSelection.Date >= start_of_week,
        MealSelection.Date <= end_of_week
    ).all()
    
    # Count unique dates where any meal was selected
    dates_with_meals = set()
    for selection in meal_selections:
        if selection.Breakfast == 'Yes' or selection.Lunch == 'Yes' or selection.Dinner == 'Yes':
            dates_with_meals.add(selection.Date)
    
    # Calculate mess bill (₹100 per day with any meal)
    mess_bill = len(dates_with_meals) * 100
    
    # Calculate total fee and balance
    total_fee = 2300 + mess_bill  # Room rent + Mess bill
    balance = total_fee - (student.PaidAmount or 0)
    
    return render_template('dues.html', 
                         student=student,
                         mess_bill=mess_bill,
                         total_fee=total_fee,
                         balance=balance)

@app.route('/submit_payment', methods=['POST'])
def submit_payment():
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        # Get form data
        transaction_id = request.form.get('transaction_id')
        payment_method = request.form.get('payment_method')
        payment_date_str = request.form.get('payment_date')
        payment_proof = request.files.get('payment_proof')
        
        # Convert payment date to 2025
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
        payment_date = payment_date.replace(year=2025)
        
        # Get student and calculate amount
        student = Student.query.get(session['student_id'])
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Get the month from the payment date
        month = payment_date.month
        year = 2025
        
        # Calculate first and last day of the payment month
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year, 12, 31).date()
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # Get meal selections for the month
        meal_selections = MealSelection.query.filter(
            MealSelection.StudentID == student.StudentID,
            MealSelection.Date >= first_day,
            MealSelection.Date <= last_day
        ).all()
        
        # Calculate mess bill
        dates_with_meals = set()
        for selection in meal_selections:
            if selection.Breakfast == 'Yes' or selection.Lunch == 'Yes' or selection.Dinner == 'Yes':
                dates_with_meals.add(selection.Date)
        
        mess_bill = len(dates_with_meals) * 100
        total_fee = 2300 + mess_bill  # Room rent + Mess bill
        
        # Create payment_proofs directory if it doesn't exist
        payment_proofs_dir = os.path.join('static', 'payment_proofs')
        if not os.path.exists(payment_proofs_dir):
            os.makedirs(payment_proofs_dir)
        
        # Save payment proof
        proof_path = None
        if payment_proof:
            # Ensure the filename is safe
            filename = f"payment_proof_{student.StudentID}_{transaction_id}.png"
            filepath = os.path.join(payment_proofs_dir, filename)
            payment_proof.save(filepath)
            proof_path = f"payment_proofs/{filename}"
        
        # Create payment record
        payment = Payment(
            StudentID=student.StudentID,
            TransactionID=transaction_id,
            PaymentMethod=payment_method,
            PaymentDate=payment_date,
            Amount=total_fee,
            Status='Pending',
            PaymentProof=proof_path
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Payment submitted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/verify_payment/<int:payment_id>', methods=['POST'])
def verify_payment(payment_id):
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Admin access required'})
    
    try:
        payment = Payment.query.get_or_404(payment_id)
        action = request.form.get('action')
        
        if action == 'verify':
            payment.Status = 'Verified'
            payment.student.PaidAmount += payment.Amount
            flash('Payment verified successfully!', 'success')
        elif action == 'reject':
            payment.Status = 'Rejected'
            flash('Payment rejected.', 'warning')
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Payment {action}ed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/pay_fee')
def pay_fee():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    
    student = Student.query.get(session['student_id'])
    if not student:
        return redirect(url_for('student_login'))
    
    # Get the requested month from query parameters, default to current month
    requested_month = request.args.get('month', datetime.now().strftime('%B'))
    month_mapping = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    current_month = month_mapping.get(requested_month, datetime.now().month)
    
    # Calculate first and last day of the selected month for 2025
    year = 2025  # Fixed year as per requirements
    first_day = datetime(year, current_month, 1).date()
    if current_month == 12:
        last_day = datetime(year, 12, 31).date()
    else:
        last_day = datetime(year, current_month + 1, 1).date() - timedelta(days=1)
    
    # Get meal selections for the selected month
    meal_selections = MealSelection.query.filter(
        MealSelection.StudentID == student.StudentID,
        MealSelection.Date >= first_day,
        MealSelection.Date <= last_day
    ).all()
    
    # Calculate mess bill based on meal selections
    # Count unique dates where any meal was selected (Breakfast, Lunch, or Dinner)
    dates_with_meals = set()
    for selection in meal_selections:
        if selection.Breakfast == 'Yes' or selection.Lunch == 'Yes' or selection.Dinner == 'Yes':
            dates_with_meals.add(selection.Date)
    
    # Calculate mess bill (₹100 per day if any meal is selected)
    mess_bill = len(dates_with_meals) * 100
    
    # Calculate total fee (room rent + mess bill)
    room_rent = 2300  # Fixed room rent
    total_fee = room_rent + mess_bill
    
    # Get transaction history for the selected month
    transactions = Payment.query.filter(
        Payment.StudentID == student.StudentID,
        Payment.PaymentDate >= first_day,
        Payment.PaymentDate <= last_day
    ).order_by(Payment.PaymentDate.desc()).all()
    
    # Get latest verified payment for the selected month
    latest_payment = Payment.query.filter(
        Payment.StudentID == student.StudentID,
        Payment.PaymentDate >= first_day,
        Payment.PaymentDate <= last_day,
        Payment.Status == 'Verified'
    ).order_by(Payment.PaymentDate.desc()).first()
    
    # Check if there's any pending payment for this month
    pending_payment = Payment.query.filter(
        Payment.StudentID == student.StudentID,
        Payment.PaymentDate >= first_day,
        Payment.PaymentDate <= last_day,
        Payment.Status == 'Pending'
    ).first()
    
    # Get all months for navigation
    months = list(month_mapping.keys())
    current_month_index = current_month - 1
    
    # Format transactions with month name
    formatted_transactions = []
    for transaction in transactions:
        formatted_transaction = {
            'PaymentID': transaction.PaymentID,
            'PaymentDate': transaction.PaymentDate,
            'Month': transaction.PaymentDate.strftime('%B'),
            'Amount': transaction.Amount,
            'Status': transaction.Status,
            'TransactionID': transaction.TransactionID,
            'PaymentMethod': transaction.PaymentMethod
        }
        formatted_transactions.append(formatted_transaction)
    
    # Calculate total paid amount for the selected month (only verified payments)
    total_paid = sum(transaction.Amount for transaction in transactions if transaction.Status == 'Verified')
    
    # Calculate remaining balance for the selected month
    remaining_balance = total_fee - total_paid
    
    # Check if payment is allowed (no pending or verified payments exist)
    payment_allowed = not (pending_payment or latest_payment)
    
    return render_template('pay_fee.html',
                         student=student,
                         mess_bill=mess_bill,
                         room_rent=room_rent,
                         total_fee=total_fee,
                         total_paid=total_paid,
                         remaining_balance=remaining_balance,
                         transactions=formatted_transactions,
                         latest_payment=latest_payment,
                         current_month=current_month,
                         months=months,
                         current_month_index=current_month_index,
                         selected_month=requested_month,
                         payment_allowed=payment_allowed,
                         pending_payment=pending_payment)

@app.route('/generate_receipt', methods=['POST'])
def generate_receipt():
    try:
        # Get receipt details from form data
        receipt_id = request.form.get('receipt_id')
        date = request.form.get('date')
        amount = request.form.get('amount')
        status = request.form.get('status')
        transaction_id = request.form.get('transaction_id')
        payment_method = request.form.get('payment_method')
        student_id = request.form.get('student_id')
        
        # Get student details
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        
        # Get current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Create a BytesIO object to store the PDF
        buffer = BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        normal_style = styles['Normal']
        
        # Create custom style for the header
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Create custom style for the receipt details
        receipt_style = ParagraphStyle(
            'ReceiptStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12
        )
        
        # Create the content
        content = []
        
        # Add header
        content.append(Paragraph("MealMate", header_style))
        content.append(Paragraph("Payment Receipt", header_style))
        content.append(Spacer(1, 20))
        
        # Add student details
        content.append(Paragraph(f"Student Name: {student.Name}", receipt_style))
        content.append(Paragraph(f"Registration Number: {student.registration_no}", receipt_style))
        content.append(Spacer(1, 10))
        
        # Add receipt details
        content.append(Paragraph(f"Receipt #{receipt_id}", receipt_style))
        content.append(Paragraph(f"Payment Date: {date}", receipt_style))
        content.append(Paragraph(f"Amount: ₹{amount}", receipt_style))
        content.append(Paragraph(f"Status: {status}", receipt_style))
        content.append(Paragraph(f"Transaction ID: {transaction_id}", receipt_style))
        content.append(Paragraph(f"Payment Method: {payment_method}", receipt_style))
        
        # Add footer
        content.append(Spacer(1, 30))
        content.append(Paragraph("Thank you for your payment!", receipt_style))
        
        # Add current date and signature
        content.append(Spacer(1, 30))
        
        # Create a table for the date and signature
        signature_data = [
            [current_date, "Sania"],
            ["Date", "Hostel Warden"]
        ]
        
        signature_table = Table(signature_data, colWidths=[2*inch, 2*inch])
        
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LINEABOVE', (0, 0), (0, 0), 1, colors.black),  # Line above date
            ('LINEABOVE', (1, 0), (1, 0), 1, colors.black),  # Line above signature
        ]))
        
        content.append(signature_table)
        
        # Build the PDF
        doc.build(content)
        
        # Get the value of the BytesIO buffer
        pdf = buffer.getvalue()
        
        # Create the response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=receipt_{date}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Run the application
if __name__ == '__main__':
    with app.app_context():
            init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
