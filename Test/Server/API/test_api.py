# Testsuite for API

from datetime import datetime
import unittest
from requests import post
import pytz
import json
from data_for_api_test import *

test_url = "http://127.0.0.1:8012/insert/"
test_url_get = "http://127.0.0.1:8012/get/"
test_url_get_latest = "http://127.0.0.1:8012/get_latest/"
test_token = 'secret_token'

class Test_api_request(unittest.TestCase):
    def test_json_to_database(self):
        headers = {
            "Authorization": f"Bearer {test_token}"
        }
        r_list = []
        for test_meas_dict in test_meas_dict_list:
            test_meas_dict['datetime'] = datetime.now(tz=pytz.utc).isoformat()
            print (f"Sended {test_meas_dict} to database")
            r = post(test_url, json=json.dumps(test_meas_dict), headers=headers)
            #r = post(test_url, json=test_meas_dict, headers=headers)
            assert r.status_code == 200, "Unexpected status code: " + str(r.status_code)

    def test_json_to_database_w_wrong_json(self):
        print(f"Sended {test_meas_dict_fail} to database with wrong json")
        headers = {
            "Authorization": f"Bearer {test_token}"
        }
        r = post(test_url, json=json.dumps(test_meas_dict_fail), headers=headers)
        # r = post(test_url, json=test_meas_dict, headers=headers)
        assert r.status_code == 406, "Unexpected status code: " + str(r.status_code)

    def test_json_to_database_w_wrong_token(self):
        headers = {
            "Authorization": f"Bearer {test_token}_wrong"
        }

        print(f"Sended {test_meas_dict_list[0]} to database with wrong token")
        r = post(test_url, json=json.dumps(test_meas_dict_list[0]), headers=headers)
        # r = post(test_url, json=test_meas_dict, headers=headers)
        assert r.status_code == 401, "Unexpected status code: " + str(r.status_code)


    def test_get_data_from_database(self):
        headers = {
            "Authorization": f"Bearer {test_token}"
        }

        test_request_dict = {
            'dt_begin': datetime(year=2024, month=12, day=1, hour=0, minute=0, second=0).isoformat(),
            'dt_end': datetime(year=2024, month=12, day=30, hour=23, minute=59, second=59).isoformat()
        }
        r = post(test_url_get, json=json.dumps(test_request_dict), headers=headers)
        print (r.json())
        assert r.status_code == 200, "Unexpected status code: " + str(r.status_code)

    def test_get_latest_data_from_database(self):
        headers = {
            "Authorization": f"Bearer {test_token}"
        }
        r = post(test_url_get_latest, headers=headers)
        #print (r.json())
        assert r.status_code == 200, "Unexpected status code: " + str(r.status_code)

if __name__ == '__main__':
    unittest.main()
