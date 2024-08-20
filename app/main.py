"""
A web interface to track MARTA car rides
"""
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
    current_file_request = requests.get(url=url)
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
        "message": "Pushed from script",
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

async def add_ride_instance(car_no: int, line: str):
    today = datetime.now().strftime("%Y-%m-%d")
    ride_to_add = {
        "car_no": car_no,
        "line": line,
        "date": today
    }
    rail_lines = load_lines()
    found_line = False
    for rail_line in rail_lines:
        if line == rail_line['shortname']:
            found_line = True
    if not found_line:
        return None


    with open(SEEN_CARS_FILE, 'a') as f:
        yaml_record = yaml.dump([ride_to_add])
        f.write(yaml_record)

    if env_vars['github']['github_enabled']:
        gihub_push = push_to_github()

    return ride_to_add

env_vars = load_env()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
