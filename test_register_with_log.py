from app import app
import logging

# Enable debug logging
app.logger.setLevel(logging.DEBUG)

# Add file handler to capture logs
handler = logging.FileHandler('registration_test.log')
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

# Run the app in debug mode
if __name__ == '__main__':
    app.run(debug=True, port=5002)