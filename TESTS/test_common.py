import unittest
import common


class TestCommon(unittest.TestCase):

    def test_int_validation(self):
        result = common.int_validation(5)
        self.assertEqual(result, [True, 5])

        result = common.int_validation(1.0)
        self.assertFalse(result[0])

        result = common.int_validation('i')
        self.assertFalse(result[0])

    def test_pure_posix_path(self):
        result = common.pure_posix_path('/home/users/patrick', 'Test', 'config.ini')
        self.assertEqual(result, '/home/users/patrick/Test/config.ini')

    def test_pure_windows_path(self):
        seeds = ('C:/', 'Users', 'User', 'AppData', 'RemoteDir', 'my remote', 'config.ini')
        result = common.pure_windows_path(*seeds)
        self.assertEqual(result, r'C:\Users\User\AppData\RemoteDir\my remote\config.ini')


if __name__ == '__main__':
    unittest.main()
