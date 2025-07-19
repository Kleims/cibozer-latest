# Manual Testing Instructions

## To test registration manually:

1. Open browser to http://localhost:5001/register
2. Fill in the form:
   - Email: test@example.com
   - Password: TestPass123!
   - Confirm Password: TestPass123!
   - Full Name: Test User
3. Click Register

## Expected Result:
- User should be registered and redirected to /create-meal-plan
- Should see success message

## Current Issue:
- Getting 500 error on registration
- CSRF token is included in form
- Need to check server logs for actual error