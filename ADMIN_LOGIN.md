# Admin Login Instructions

## Admin Account Credentials

**Username:** `admin`  
**Password:** `admin123`

## How to Access

1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to the login page:
   - URL: `http://localhost:8000/login/`
   - Or click "Login" from the home page

3. Enter the credentials above

4. After successful login, you will be automatically redirected to:
   - **Admin Panel:** `/admin-page/`

## Admin Panel Features

The admin panel allows you to:
- View all **Students** with their usernames and likely passwords
- View all **Instructors** with their usernames and likely passwords  
- View all **Department Heads** with their usernames and likely passwords
- See user counts for each category

## Creating Additional Admin Users

To create more admin users, run:
```bash
python manage.py create_admin
```

Or use Django's built-in command:
```bash
python manage.py createsuperuser
```

## Notes

- Passwords are stored securely as hashes in Django
- The passwords shown in the admin panel are likely default/test passwords based on common patterns
- Users should change their passwords after first login for security

