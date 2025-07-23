"""Application entry point for refactored Cibozer."""
import os
from app import create_app, db
from app.models import User

# Create application
app = create_app()

# Shell context for flask shell
@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell."""
    return {
        'db': db,
        'User': User,
    }

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )