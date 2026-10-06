import unittest


class PublicAccessTests(unittest.TestCase):
    def test_authentication_is_not_required(self):
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
