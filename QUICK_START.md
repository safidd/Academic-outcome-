# Quick Start Guide - All Users Ready to Login

## ✅ Setup Complete

All users have been configured and are ready to log in. Here's what's been done:

1. ✅ All 23 users have passwords set
2. ✅ All users are active
3. ✅ Login redirects are configured
4. ✅ Dashboards are accessible for each role

## Login Instructions

### Step 1: Start the Server
```bash
cd /Users/macbookpro14/Desktop/MVP
source venv/bin/activate
python manage.py runserver
```

### Step 2: Access Login Page
Navigate to: `http://localhost:8000/login/`

### Step 3: Use Credentials

**For Students:**
- Username: Any student username (e.g., `alex.johnson`)
- Password: `student123`
- Redirects to: `/student/dashboard/`

**For Instructors:**
- Username: Any instructor username (e.g., `instructor1`, `sarah.anderson`)
- Password: `instructor123`
- Redirects to: `/instructor/dashboard/`

**For Department Heads:**
- Username: `head1`
- Password: `head123`
- Redirects to: `/head/dashboard/`

**For Admin:**
- Username: `admin`
- Password: `admin123`
- Redirects to: `/admin-page/`

## All Available Users

See `USER_CREDENTIALS.md` for the complete list of all 23 users with their credentials.

## Troubleshooting

If a user cannot log in:

1. **Reset all passwords:**
   ```bash
   python manage.py setup_all_passwords
   ```

2. **Verify user exists:**
   ```bash
   python manage.py shell
   >>> from users.models import CustomUser
   >>> CustomUser.objects.filter(username='username_here')
   ```

3. **Check if user is active:**
   ```bash
   python manage.py shell
   >>> from users.models import CustomUser
   >>> user = CustomUser.objects.get(username='username_here')
   >>> user.is_active  # Should be True
   ```

## Dashboard URLs

- Student Dashboard: `http://localhost:8000/student/dashboard/`
- Instructor Dashboard: `http://localhost:8000/instructor/dashboard/`
- Department Head Dashboard: `http://localhost:8000/head/dashboard/`
- Admin Panel: `http://localhost:8000/admin-page/`

All dashboards are protected and will redirect to login if not authenticated.

