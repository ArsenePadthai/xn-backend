import unittest
from XNBackend.app.factory import create_app, db
from XNBackend.tasks.utils import get_mantunsci_addr_mapping


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.app = create_app('../testing.cfg')
        with self.app.app_context():
            db.create_all()

    def test_get_mantunsci_addr_mapping(self):
        with self.app.app_context():
            m = get_mantunsci_addr_mapping()
            assert m['187ED531DCF0'][1] == ['301', 1]

    def tearDown(self):
        with self.app.app_context():
            pass


if __name__ == '__main__':
    unittest.main()
