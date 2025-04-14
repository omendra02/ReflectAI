from app import app, db
from app.models import User, JournalEntry

with app.app_context():
    # Create all database tables
    db.create_all()
    print("Database tables created successfully!")

    # Create a test user if it doesn't exist
    if not User.query.filter_by(username="test").first():
        test_user = User(username="test", email="test@example.com")
        test_user.set_password("test123")
        db.session.add(test_user)
        db.session.commit()
        print("Test user created successfully!") 