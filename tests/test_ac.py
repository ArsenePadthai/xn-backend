import unittest
# from XNBackend.app.entry import app
from XNBackend.api_client.air_conditioner import set_ac_data


class BasicTest(unittest.TestCase):

    def setUp(self):
        self.device_index_code = '4104'
        self.data_to_set = {
            "FanSpeedSet": 3,
            "ModeCmd": 4,
            "StartStopStatus": 1,
            "TempSet": 23
        }

    def test_set_ac(self):
        ret = set_ac_data(self.device_index_code, **self.data_to_set)
        self.assertEqual(ret['writeResult'],
                         {"FanSpeedSet": 0, "ModeCmd": 0, "StartStopStatus": 0, "TempSet": 0})

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
