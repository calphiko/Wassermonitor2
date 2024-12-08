# Testsuite for API

from datetime import datetime
import unittest
from requests import post
import pytz
import json

test_url = "http://127.0.0.1:8012/insert/"
test_token = 'secret_token'

test_meas_dict = {
    'datetime': datetime.now(tz=pytz.utc).isoformat(),
    'pi_name': 'measurement_pi_1',
    'sensor_id': 5,
    'values': [
        1.34562,
        1.34561,
        1.34562,
        1.34563,
        1.345625
    ]
}

test_meas_dict_fail = {
    'datetime': datetime.now(tz=pytz.utc).isoformat(),
    'pi_name': 'measurement_pi_1',
    'sensor_id': 5,
    'values': [
        ';DROP DATABASE BLA BLA',
        1.34561,
        1.34562,
        1.34563,
        1.345625
    ]
}

class Test_api_request(unittest.TestCase):
    def test_json_to_database(self):
        headers = {
            "Authorization": f"Bearer {test_token}"
        }

        print (f"Sended {test_meas_dict} to database")
        r = post(test_url, json=json.dumps(test_meas_dict), headers=headers)
        #r = post(test_url, json=test_meas_dict, headers=headers)
        assert r.status_code == 200, "Unexpected status code: " + str(r.status_code)

    def test_json_to_database_w_wrong_json(self):
        print(f"Sended {test_meas_dict} to database with wrong json")
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

        print(f"Sended {test_meas_dict} to database with wrong token")
        r = post(test_url, json=json.dumps(test_meas_dict), headers=headers)
        # r = post(test_url, json=test_meas_dict, headers=headers)
        assert r.status_code == 401, "Unexpected status code: " + str(r.status_code)




if __name__ == '__main__':
    unittest.main()
