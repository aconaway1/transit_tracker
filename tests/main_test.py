import unittest
import requests

BASE_URL = "http://localhost:8000"
TEST_CAR_NO = "999999"
TEST_RIDE_LINE = "reds"

class TestMainClass(unittest.TestCase):
    def test_home(self):
        status_code = requests.get(url=BASE_URL).status_code
        self.assertEqual(status_code, 200)

    def test_add_ride(self):
        contents=f"car_no={TEST_CAR_NO}&line={TEST_RIDE_LINE}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        status_code = requests.post(url=f"{BASE_URL}/add_ride", data=contents, headers=headers).status_code
        self.assertEqual(status_code, 200)

    def test_all_lines(self):
        status_code = requests.get(url=f"{BASE_URL}/lines").status_code
        self.assertEqual(status_code, 200)
    def test_a_ride(self):
        status_code = requests.get(url=f"{BASE_URL}/rides/{TEST_CAR_NO}").status_code
        self.assertEqual(status_code, 200)

    def test_all_rides(self):
        status_code = requests.get(url=f"{BASE_URL}/rides").status_code
        self.assertEqual(status_code, 200)


    def test_stock(self):
        status_code = requests.get(url=f"{BASE_URL}/stock").status_code
        self.assertEqual(status_code, 200)

    def test_scrub(self):
        status_code = requests.get(url=f"{BASE_URL}/scrub").status_code
        self.assertEqual(status_code, 200)