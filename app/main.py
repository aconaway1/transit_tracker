"""
A web interface to track MARTA car rides
"""
import pprint
from datetime import datetime
from typing import Annotated
import yaml
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import base64
import hashlib
import json

ENV_FILE = "env.yml"
LINE_FILE = "linedata.yml"
SEEN_CARS_FILE = "/code/data/seen_cars.yml"
CAR_NO_LIMIT = 9999


def load_lines() -> list:
    with open(LINE_FILE, encoding="utf8") as file:
        return yaml.safe_load(file)

def load_env():
    """
    Load the environment
    """
    with open(ENV_FILE, encoding="utf8") as file:
        return yaml.safe_load(file)

def get_rides() -> list:
    with open(SEEN_CARS_FILE, encoding="utf8") as file:
        return yaml.safe_load(file)

def get_a_ride(queried_car_no: int) -> list :
    seen_car_records = []
    with open(SEEN_CARS_FILE, encoding="utf8") as file:
        seen_cars = yaml.safe_load(file)
    for seen_car in seen_cars:
        if seen_car['car_no'] == queried_car_no:
            seen_car_records.append(seen_car)
    return seen_car_records

def push_to_github():
    TOKEN = env_vars['github']['github_api_token']
    USERNAME = env_vars['github']['github_username']
    REPO_NAME = env_vars['github']['github_repo_name']
    BASE_URL = env_vars['github']['github_base_url']

    url = f"{BASE_URL}/repos/{USERNAME}/{REPO_NAME}/contents/seen_cars.yml"

    # Get the current SHA
    try:
        current_file_request = requests.get(url=url)
    except requests.exceptions.RequestException:
        send_slack_msg(f"Couldn't commit to GitHub for some reason.\n{current_file_request.content}")

    if current_file_request.status_code != 200:
        send_slack_msg(f"This doesn't look right at all!\n{send_slack_msg(current_file_request.content)}")
        return None

    sha = current_file_request.json()['sha']

    try:
        with open(SEEN_CARS_FILE, encoding="utf8") as f:
            content_string = f.read()
    except FileNotFoundError:
        print(f"The file {SEEN_CARS_FILE} wasn't found.")
        return None

    encoded_content = content_string.encode('ascii')
    b64_content = base64.b64encode(encoded_content)

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    body = {
        "message": "Updated from transit_tracker API",
        "contributor": {
            "name": "Aaron Conaway",
            "email": "aaron@aconaway.com",
        },
        "content": b64_content.decode(),
        "sha": sha
    }
    sha = hashlib.sha1()

    returned_data = requests.put(url=url, headers=headers, data=json.dumps(body))

    return returned_data


def send_slack_msg(message: str):

    headers = {
        "Content-type": "application/json"
    }

    body = {
        "text": message,
    }

    slack_request = requests.post(
        url=env_vars['slack']['slack_incoming_webhook'],
        headers=headers,
        data=json.dumps(body)
    )

    if slack_request.status_code != 200:
        raise ValueError(
        'Request to slack returned an error %s, the response is:\n%s'
        % (response.status_code, response.text)
    )

    return slack_request

async def add_ride_instance(car_no: int, line: str):
    today = datetime.now().strftime("%Y-%m-%d")
    ride_to_add = {
        "car_no": car_no,
        "line": line,
        "date": today
    }
    rail_lines = load_lines()
    found_line = False
    long_line_name = ""
    for rail_line in rail_lines:
        if line == rail_line['shortname']:
            found_line = True
            long_line_name = rail_line['longname']
    if not found_line:
        return None


    with open(SEEN_CARS_FILE, 'a') as f:
        yaml_record = yaml.dump([ride_to_add])
        f.write(yaml_record)

    if env_vars['github']['github_enabled']:
        gihub_push = push_to_github()

    if env_vars['slack']['slack_enabled']:
        slack_reply = send_slack_msg(f"Added {car_no} on line {long_line_name} at {today}.")

    return ride_to_add

def update_from_github():
    TOKEN = env_vars['github']['github_api_token']
    USERNAME = env_vars['github']['github_username']
    REPO_NAME = env_vars['github']['github_repo_name']
    BASE_URL = env_vars['github']['github_base_url']

    url = f"{BASE_URL}/repos/{USERNAME}/{REPO_NAME}/contents/seen_cars.yml"

    # Get the current SHA
    try:
        updated_file_request = requests.get(url=url)
    except requests.exceptions.RequestException:
        send_slack_msg(f"Couldn't get the file from GitHub for some reason.\n{updated_file_request.content}")
        return None

    if updated_file_request.status_code != 200:
        send_slack_msg(f"Something went wrong with updating from Github!\n{send_slack_msg(updated_file_request.content)}")
        return None

    returned_content = updated_file_request.json()['content']
    returned_content = base64.b64decode(returned_content)
    returned_content = returned_content.decode('ascii')

    print(f"{returned_content=}")
    print(f"{type(returned_content)=}")

    loaded_yaml = yaml.safe_load(returned_content)
    with open(SEEN_CARS_FILE, encoding="utf8", mode='w') as f:
        for ride in loaded_yaml:
            yaml_record = yaml.dump([ride])
            f.write(yaml_record)

    return returned_content

env_vars = load_env()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    if env_vars['github']['github_download_on_startup'] and env_vars['github']['github_enabled']:
        response = update_from_github()

@app.get('/', response_class=HTMLResponse)
async def main(request: Request):
    """
    Show a form when / is called via get
    """
    lines = load_lines()
    return templates.TemplateResponse(request=request, name="add_ride.j2", context={"lines": lines})


@app.get('/rides')
async def get_all_rides():
    """
    Show the user the cars observed
    """
    return get_rides()


@app.get('/rides/{car_no}')
async def get_car(car_no):
    """
    Show the user a specific car observed
    """
    return get_a_ride(queried_car_no=car_no)


@app.get('/lines')
async def get_lines():
    """
    Show the user the lines available
    """
    return load_lines()

@app.post('/add_ride')
async def add_ride(request: Request, car_no: Annotated[str, Form()], line: Annotated[str, Form()]):
    return_status = await add_ride_instance(car_no, line)
    if return_status:
        # return HTMLResponse(f"You observed car {car_no} on line {line}.")
        lines = load_lines()
        return templates.TemplateResponse(request=request, name="add_ride.j2", context={"lines": lines, "status": f"Added {car_no} on {line}"})
    else:
        return False


@app.get('/report')
async def ride_report(request: Request):
    ride_data = []
    rail_lines = load_lines()
    with open(SEEN_CARS_FILE, encoding="utf8") as file:
        seen_cars = yaml.safe_load(file)

    for ride in seen_cars:
        found_line = False
        long_line = ""
        for rail_line in rail_lines:
            if str(ride['line']) == rail_line['shortname']:
                long_line = rail_line['longname']
                found_line = True
        if found_line:
            ride_record = {"car_no": ride['car_no'], "date": ride['date'], "line": long_line}
        else:
            ride_record = ride
        ride_data.append(ride_record)

    sorted_list = sorted(ride_data, key=lambda x: x['car_no'])

    return templates.TemplateResponse(request=request, name="ride_report.j2", context={"rides": sorted_list})

@app.get('/scrub/')
async def scrub_test_rides(request: Request):
    valid_rides = []
    scrubbed_rides = []
    rides = get_rides()

    for ride in rides:
        if int(ride['car_no']) > CAR_NO_LIMIT:
            send_slack_msg(f"Car number {ride['car_no']} is not valid. Removing")
            scrubbed_rides.append(ride)
            continue
        else:
            valid_rides.append(ride)

    with open(SEEN_CARS_FILE, encoding="utf8", mode='w') as f:
        for ride in valid_rides:
            yaml_record = yaml.dump([ride])
            f.write(yaml_record)

    if scrubbed_rides:
        return {"message": f"Scrubbed values above {CAR_NO_LIMIT}",
                "values": scrubbed_rides}
    else:
        return {"message": "No rides scrubbed."}


@app.get('/stock')
async def stock_report():
    rides = get_rides()
    stock_count = {
        "CQ310": 0,
        "CQ311": 0,
        "CQ312": 0,
        "CQ400": 0
    }
    for ride in rides:
        if int(ride['car_no']) >= 101 and int(ride['car_no']) <= 200:
            stock_count['CQ310'] += 1
        if int(ride['car_no']) >= 501 and int(ride['car_no']) <= 520:
            stock_count['CQ310'] += 1
        if int(ride['car_no']) >= 201 and int(ride['car_no']) <= 320:
            stock_count['CQ311'] += 1
        if int(ride['car_no']) >= 601 and int(ride['car_no']) <= 664:
            stock_count['CQ312'] += 1
        if int(ride['car_no']) >= 667 and int(ride['car_no']) <= 702:
            stock_count['CQ312'] += 1

    return {"CQ310": stock_count["CQ310"], "CQ311": stock_count["CQ311"], "CQ312": stock_count["CQ312"]}

@app.get("/ping")
async def ping():
    return {"message": "pong"}