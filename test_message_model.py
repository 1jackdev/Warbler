"""Message model tests."""


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

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
    """Test model for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.userid = 40
        user = User.signup(username='message', password='password',
                           email="message@gmail.com", image_url=None)
        user.id = self.userid
        db.session.commit()

        self.user = User.query.get_or_404(self.userid)

        
    def tearDown(self):
        td = super().tearDown()
        db.session.rollback()
        return td

    def test_message_model(self):
        """Does basic message model work?"""

        msg = Message(
            text="a warble",
            user_id=self.userid
        )

        db.session.add(msg)
        db.session.commit()

        # User should have 1 message
        self.assertEqual(len(self.user.messages), 1)

    def test_message_likes(self):
        msg1 = Message(
            text="a warble",
            user_id=self.userid
        )

        msg2 = Message(
            text="a very interesting warble",
            user_id=self.userid
        )

        user2 = User.signup(
            username="message2", email="test@email.com", password="password", image_url=None)
        user2id = 50
        user2.id = user2id
        db.session.add_all([msg1, msg2, user2])
        db.session.commit()

        user2.likes.append(msg1)

        db.session.commit()

        like = Likes.query.filter(Likes.user_id == user2id).all()
        self.assertEqual(len(like), 1)

