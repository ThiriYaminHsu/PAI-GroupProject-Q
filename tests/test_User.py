import unittest

# import models
from src.models.User import User
from src.models.UserRole import UserRole

class TestUserModel(unittest.TestCase):
    
    def setUp(self):
        # setup test user instance #
        self.user = User(
            user_id="u1001",
            first_name="John",
            lastname="Doge",
            password_hash="hashed_secret",
            role=UserRole.STUDENT
        )

    def test_initialization(self):
        # test data class initialization #
        self.assertEqual(self.user.user_id, "u1001")
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.role, UserRole.STUDENT)

    def test_equality(self):
        # test @dataclass auto generated equality #
        # same data object #
        same_user = User("u1001", "John", "Doge", "hashed_secret", UserRole.STUDENT)
        # different data object #
        diff_user = User("u1002", "Jane", "Doge", "hashed_secret", UserRole.STUDENT)
        
        self.assertEqual(self.user, same_user, "same data user should be equal")
        self.assertNotEqual(self.user, diff_user, "different id user should not be equal")

    def test_permission_student(self):
        # test student permission #
        student = User("u100", "Sam", "Smith", "hash", UserRole.STUDENT)
        self.assertFalse(student.can_view_personal_wellbeing())
    
    def test_permission_officer(self):
        # test wellbeing officer permission #
        officer = User("u200", "Alice", "Smith", "hash", UserRole.WELLBEING_OFFICER)
        self.assertTrue(officer.can_view_personal_wellbeing())

    def test_permission_admin(self):
        # test admin permission #
        admin = User("u300", "Bob", "Admin", "hash", UserRole.ADMIN)
        self.assertTrue(admin.can_view_personal_wellbeing())

if __name__ == '__main__':
    unittest.main()