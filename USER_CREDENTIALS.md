# User Login Credentials

All users are now set up and ready to log in. Use these credentials to access their respective dashboards.

## Admin Account
- **Username:** `admin`
- **Password:** `admin123`
- **Access:** Admin Panel (`/admin-page/`)

## Students (15 users)
All students use password: **`student123`**

| Username | Full Name | Email |
|----------|-----------|-------|
| alex.johnson | Alex Johnson | alex.johnson@student.university.edu |
| maria.garcia | Maria Garcia | maria.garcia@student.university.edu |
| david.brown | David Brown | david.brown@student.university.edu |
| jennifer.davis | Jennifer Davis | jennifer.davis@student.university.edu |
| robert.miller | Robert Miller | robert.miller@student.university.edu |
| jessica.martinez | Jessica Martinez | jessica.martinez@student.university.edu |
| christopher.garcia | Christopher Garcia | christopher.garcia@student.university.edu |
| amanda.rodriguez | Amanda Rodriguez | amanda.rodriguez@student.university.edu |
| daniel.lewis | Daniel Lewis | daniel.lewis@student.university.edu |
| ashley.lee | Ashley Lee | ashley.lee@student.university.edu |
| matthew.walker | Matthew Walker | matthew.walker@student.university.edu |
| emily.hall | Emily Hall | emily.hall@student.university.edu |
| andrew.allen | Andrew Allen | andrew.allen@student.university.edu |
| michelle.young | Michelle Young | michelle.young@student.university.edu |
| joshua.king | Joshua King | joshua.king@student.university.edu |

**Dashboard URL:** `/student/dashboard/`

## Instructors (6 users)
All instructors use password: **`instructor123`**

| Username | Full Name | Email |
|----------|-----------|-------|
| instructor1 | - | instructor1@example.com |
| sarah.anderson | Dr. Sarah Anderson | sarah.anderson@university.edu |
| michael.chen | Dr. Michael Chen | michael.chen@university.edu |
| emily.rodriguez | Dr. Emily Rodriguez | emily.rodriguez@university.edu |
| james.wilson | Dr. James Wilson | james.wilson@university.edu |
| lisa.thompson | Dr. Lisa Thompson | lisa.thompson@university.edu |

**Dashboard URL:** `/instructor/dashboard/`

## Department Heads (1 user)
All department heads use password: **`head123`**

| Username | Full Name | Email |
|----------|-----------|-------|
| head1 | - | head1@example.com |

**Dashboard URL:** `/head/dashboard/`

## How to Log In

1. Start the server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to: `http://localhost:8000/login/`

3. Enter username and password from the table above

4. You will be automatically redirected to:
   - **Students** → `/student/dashboard/`
   - **Instructors** → `/instructor/dashboard/`
   - **Department Heads** → `/head/dashboard/`
   - **Admin** → `/admin-page/`

## Notes

- All passwords have been set and are ready to use
- Users are automatically redirected to their role-specific dashboard after login
- If you see any issues, run: `python manage.py setup_all_passwords` to reset all passwords

