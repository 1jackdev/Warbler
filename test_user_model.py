"""User model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test2"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup(username='user1', password='password', image_url=None)
        user1id = 20
        user1.id = user1id
        
        user2 = User.signup(username='user2', password='password', image_url=None)
        user2id = 30
        user2.id = user2id

        db.session.commit()

        user1 = User.query.get_or_404(user1id)
        user2 = User.query.get_or_404(user2id)

        self.user1 = user1
        self.user1id = user1id

        self.user2 = user2
        self.user2id = user2id


        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()
        return super().tearDown()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)