"""User model tests."""


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
    """Test model for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        user1 = User.signup(username='user1', password='password',
                            email="1@gmail.com", image_url=None)
        user1id = 20
        user1.id = user1id

        user2 = User.signup(username='user2', password='password',
                            email="2@gmail.com",  image_url=None)
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
        td = super().tearDown()
        db.session.rollback()
        return td

    def test_user_model(self):
        """Does basic user model work?"""

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

    def test_user_follows(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user2.following), 0)
        self.assertEqual(len(self.user2.followers), 1)
        self.assertEqual(len(self.user1.followers), 0)
        self.assertEqual(len(self.user1.following), 1)

        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        self.assertEqual(self.user1.following[0].id, self.user2.id)

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))

    ####
    #
    # Signup Tests
    #
    ####
    def test_valid_signup(self):
        user_test = User.signup(username="testtesttest", email="testtest@test.com", password="password", image_url=None)
        user_testid = 99999
        user_test.id = user_testid
        db.session.commit()

        user_test = User.query.get(user_testid)
        self.assertIsNotNone(user_test)
        self.assertEqual(user_test.username, "testtesttest")
        self.assertEqual(user_test.email, "testtest@test.com")
        self.assertNotEqual(user_test.password, "password")

    def test_invalid_username_signup(self):
        invalid_user = User.signup(username=None, email="test@test.com", password="password", image_url=None)
        invalid_userid = 123456789
        invalid_user.id = invalid_userid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup(username="testtest", email="email@email.com", password="", image_url=None)
        
        with self.assertRaises(ValueError) as context:
            User.signup(username="testtest", email="email@email.com", password=None, image_url=None)
    
    ####
    #
    # Authentication Tests
    #
    ####
    def test_valid_authentication(self):
        user = User.authenticate(username=self.user1.username, password="password")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user1id)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate(username="badusername", password="password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(username=self.user1.username, password="badpassword"))
