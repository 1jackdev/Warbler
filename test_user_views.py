"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py



import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test2"


# Now we can import app
from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.testuser = User.signup(username="test",
                                    email="test@gmail.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 300
        self.testuser.id = self.testuser_id

        self.user1 = User.signup("abc", "test1@test.com", "password", None)
        self.user1_id = 100
        self.user1.id = self.user1_id

        self.user2 = User.signup("efg", "test2@test.com", "password", None)
        self.user2_id = 200
        self.user2.id = self.user2_id
        

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        td = super().tearDown()
        db.session.rollback()
        return td

    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@test", str(resp.data))
            self.assertIn("@abc", str(resp.data))
            self.assertIn("@efg", str(resp.data))

    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@test", str(resp.data))    

            self.assertNotIn("@abc", str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test", str(resp.data))

    def setup_likes(self):
        msg1 = Message(id=4, text="i warble", user_id=self.testuser_id)
        msg2 = Message(id=5, text="you warble", user_id=self.user1_id)
        db.session.add_all([msg1, msg2])
        db.session.commit()

        like = Likes(user_id=self.testuser_id, message_id=5)

        db.session.add(like)
        db.session.commit()

    def test_user_show_with_likes(self):
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 1 message
            self.assertIn("1", found[0].text)

            # Test for a count of 0 followers
            self.assertIn("0", found[1].text)

            # Test for a count of 0 following
            self.assertIn("0", found[2].text)

            # Test for a count of 1 like
            self.assertIn("1", found[3].text)

    def test_add_like(self):
        msg = Message(id=10, text="he warbles", user_id=self.user1_id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/messages/add_like/10", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==10).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_remove_like(self):
        self.setup_likes()

        msg = Message.query.filter(Message.text=="you warble").one()
        self.assertIsNotNone(msg)
        self.assertNotEqual(msg.user_id, self.testuser_id)

        like = Likes.query.filter(
            Likes.user_id==self.testuser_id and Likes.message_id==msg.id
        ).one()

        # Now we are sure that testuser likes the message "likable warble"
        self.assertIsNotNone(like)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f"/messages/add_like/{msg.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==msg.id).all()
            # the like has been deleted
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        self.setup_likes()

        msg = Message.query.filter(Message.text=="i warble").one()
        self.assertIsNotNone(msg)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/add_like/{msg.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.user1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.user2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.user1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_user_show_with_follows(self):

        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 messages
            self.assertIn("0", found[0].text)

            # Test for a count of 2 following
            self.assertIn("2", found[1].text)

            # Test for a count of 1 follower
            self.assertIn("1", found[2].text)

            # Test for a count of 0 likes
            self.assertIn("0", found[3].text)

    def test_show_following(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@abc", str(resp.data))
            self.assertIn("@efg", str(resp.data))


    def test_show_followers(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("@abc", str(resp.data))
            self.assertNotIn("@efg", str(resp.data))

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@abc", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@abc", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))