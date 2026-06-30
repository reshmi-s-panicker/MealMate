# MEAL MATES - Hostel Mess Management System

A modern web-based solution for managing hostel mess operations, making meal management seamless for both students and administrators. MEAL MATES simplifies daily meal planning, tracking, and payments in educational hostels.

## Overview
MEAL MATES is a comprehensive Hostel Mess Management System designed to streamline the meal management process for students living in hostels. This web application provides an efficient way to manage student registrations, meal selections, menu planning, feedback collection, and fee payments.

## Features

### For Students
- **User Authentication**: Secure login system for students
- **Meal Selection**: Easy selection of daily meals (Breakfast, Lunch, Dinner)
- **Weekly Menu**: View the weekly mess menu
- **Fee Payment**: Online payment system with receipt generation
- **Feedback System**: Submit feedback and ratings for meals
- **Profile Management**: Update personal details and view payment history

### For Administrators
- **Student Management**: Add, view, and manage student records
- **Menu Management**: Create and update weekly menus
- **Payment Verification**: Verify and track student payments
- **Feedback Analysis**: View and analyze student feedback
- **Report Generation**: Generate reports for meal selections and payments

## Technology Stack
- **Backend**: Python with Flask framework
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **PDF Generation**: ReportLab for generating payment receipts
- **Authentication**: Secure password hashing with Werkzeug

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Setup Instructions
1. Clone the repository:
   ```bash
   git clone [your-repository-url]
   cd MEAL-MATES
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```python
   python init_db.py
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Access the application at `http://localhost:5000`

## Default Credentials

### Admin
- **Email**: sania@admin.com
- **Password**: sania123

### Student
- **Email**: student@example.com
- **Password**: student123

## Project Structure
```
MEAL-MATES/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/             # HTML templates
│   ├── admin/
│   └── student/
└── instance/
    └── db.sqlite3        # SQLite database
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Contact
For any queries or support, please contact reshmispanicker08@gmail.com
