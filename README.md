# Academic Outcome Tracker

A Django-based academic outcome tracking system with role-based access control.

## Features

- **Three User Roles:**
  - Student
  - Instructor
  - Department Head

- **Database Models:**
  - CustomUser (with role field)
  - Course (name, code, instructor)
  - LearningOutcome (code, description, course)
  - ProgramOutcome (code, description)
  - ContributionRate (mapping between Learning Outcomes and Program Outcomes)
  - Grade (student, course, learning_outcome, score)

- **Role-Based Dashboards:**
  - `/student/dashboard/` - Student dashboard
  - `/instructor/dashboard/` - Instructor dashboard
  - `/head/dashboard/` - Department Head dashboard

- **Access Restrictions:**
  - Each role can only access their own dashboard
  - Students cannot access instructor or head dashboards
  - Instructors cannot access student or head dashboards
  - Department Heads cannot access student or instructor dashboards

## Setup Instructions

1. **Activate Virtual Environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser (for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Create Sample Users:**
   Use the Django admin at `http://127.0.0.1:8000/admin/` to create users with different roles:
   - Create a user with role: `student`
   - Create a user with role: `instructor`
   - Create a user with role: `department_head`

6. **Run Development Server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the Application:**
   - Home page: `http://127.0.0.1:8000/`
   - Login: `http://127.0.0.1:8000/login/`
   - Admin: `http://127.0.0.1:8000/admin/`

## Testing Login

After creating users through the admin:

1. Go to `http://127.0.0.1:8000/login/`
2. Log in with a user of each role
3. You will be automatically redirected to the appropriate dashboard:
   - Students → `/student/dashboard/`
   - Instructors → `/instructor/dashboard/`
   - Department Heads → `/head/dashboard/`

## Database Models

All models are registered in the Django admin for easy management:

- **Users** - Manage users and their roles
- **Courses** - Create and manage courses
- **Learning Outcomes** - Define learning outcomes for courses
- **Program Outcomes** - Define program-level outcomes
- **Contribution Rates** - Map learning outcomes to program outcomes
- **Grades** - Record student grades for learning outcomes

## Project Structure

```
academic_tracker/
├── academic_tracker/     # Main project settings
├── users/                # User authentication and CustomUser model
├── courses/              # Course model and instructor dashboard
├── outcomes/             # LearningOutcome, ProgramOutcome, ContributionRate models and head dashboard
├── grades/               # Grade model and student dashboard
└── manage.py
```

