"""
A web interface to track MARTA car rides
"""
import re
from datetime import datetime
from typing import Annotated
import base64
import hashlib
import json
import requests
import yaml
from fastapi import FastAPI, Request, Form, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from mastodon import Mastodon


ENV_FILE = "env.yml"
LINE_FILE = "linedata.yml"
SEEN_CARS_FILE = "/code/data/seen_cars.yml"
CAR_NO_LIMIT = 9999
CONN_TIMEOUT = 10

APP_NAME = "Aaron's Transit Tracker"
APP_VERSION = "1.1.1"


def load_lines() -> list:
    """
    Return the list of rail lines from LINE_FILE
    """
    with open(LINE_FILE, encoding="utf8") as file:
        return yaml.safe_load(file)

def load_env():
    """
    Load the environment
    """
    with open(ENV_FILE, encoding="utf8") as file:
        return yaml.safe_load(file)

def get_rides() -> list:
    """
    Return the list of rides from SEEN_CARS_FILE
    """
    with open(SEEN_CARS_FILE, encoding="utf8") as file:
        return yaml.safe_load(file)

def get_rides_on_a_car(queried_car_no: int) -> list :
    """
    Return a list of rides on a particular car
    """
    seen_car_records = []
    with open(SEEN_CARS_FILE, encoding="utf8") as file:
        seen_cars = yaml.safe_load(file)
    for seen_car in seen_cars:
        if seen_car['car_no'] == queried_car_no:
            seen_car_records.append(seen_car)
    return seen_car_records

def push_to_github():
    """
    Push the new SEEN_CARS_FILE to the GitHub repo
    """
    token = env_vars['github']['github_api_token']
    username = env_vars['github']['github_username']
    repo_name = env_vars['github']['github_repo_name']
    base_url = env_vars['github']['github_base_url']

    url = f"{base_url}/repos/{username}/{repo_name}/contents/seen_cars.yml"

    # Get the current SHA
    try:
        current_file_request = requests.get(url=url, timeout=CONN_TIMEOUT)
    except requests.exceptions.RequestException:
        send_slack_msg("Couldn't commit to GitHub for some reason.\n")
        return None

    if current_file_request.status_code != 200:
        send_slack_msg(f"This doesn't look right at all!\n"
                       f"{send_slack_msg(current_file_request.content)}")
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
        "Authorization": f"Bearer {token}",
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

    returned_data = requests.put(url=url, headers=headers, data=json.dumps(body),
                                 timeout=CONN_TIMEOUT)

    return returned_data


def send_slack_msg(message: str):
    """
    Send a message to Slack
    """
    headers = {
        "Content-type": "application/json"
    }

    body = {
        "text": message,
    }

    slack_request = requests.post(
        url=env_vars['slack']['slack_incoming_webhook'],
        headers=headers,
        data=json.dumps(body),
        timeout=CONN_TIMEOUT
    )

    if slack_request.status_code != 200:
        raise ValueError(
        f'Request to slack returned an error. The response is:\n'
        f'{slack_request.status_code, slack_request.text}'
    )

    return slack_request

async def get_line_longname(shortname):
    """
    Return the long name (eg., "Red South") from the shortname (eg. "reds")
    """
    rail_lines = load_lines()
    for rail_line in rail_lines:
        if shortname == rail_line['shortname']:
            return rail_line['longname']
    return None

async def add_ride_instance(car_no: int, line: str):
    """
    Add a ride to the SEEN_CARS_FILE
    """
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

    with open(SEEN_CARS_FILE, 'a', encoding="utf8") as f:
        yaml_record = yaml.dump([ride_to_add])
        f.write(yaml_record)

    if env_vars['github']['github_enabled']:
        gihub_push = push_to_github()

    if env_vars['slack']['slack_enabled']:
        if int(car_no) < CAR_NO_LIMIT:
            slack_reply = send_slack_msg(f"Added {car_no} on line {long_line_name} at {today}.")
        else:
            slack_reply = send_slack_msg(f"TEST: Added {car_no} on line {long_line_name} "
                                         f"at {today}.")

    if env_vars['mastodon']['mastodon_enabled'] and int(car_no) < CAR_NO_LIMIT:
        long_line = await get_line_longname(line)
        line_name, direction = long_line.split(" ")
        render_data = {"car_no": car_no, "line": line_name, "direction": direction.lower()}
        post_template = templates.get_template("toot.j2")
        rendered_msg = post_template.render(render_data)
        masto_conn = Mastodon(access_token=env_vars['mastodon']['mastodon_token'],
                              api_base_url=env_vars['mastodon']['mastodon_base_url'])
        toot_result = masto_conn.status_post(rendered_msg)

    return ride_to_add

def update_from_github():
    """
    Pull down a fresh SEEN_CARS_FILE from GitHub
    """
    # TOKEN = env_vars['github']['github_api_token']
    username = env_vars['github']['github_username']
    repo_name = env_vars['github']['github_repo_name']
    base_url = env_vars['github']['github_base_url']

    url = f"{base_url}/repos/{username}/{repo_name}/contents/seen_cars.yml"

    # Get the current SHA
    try:
        updated_file_request = requests.get(url=url, timeout=CONN_TIMEOUT)
    except requests.exceptions.RequestException:
        send_slack_msg("Couldn't get the file from GitHub for some reason.")
        return None

    if updated_file_request.status_code != 200:
        send_slack_msg(f"Something went wrong with updating from Github!\n"
                       f"{send_slack_msg(updated_file_request.content)}")
        return None

    returned_content = updated_file_request.json()['content']
    returned_content = base64.b64decode(returned_content)
    returned_content = returned_content.decode('ascii')

    loaded_yaml = yaml.safe_load(returned_content)
    with open(SEEN_CARS_FILE, encoding="utf8", mode='w') as f:
        for ride in loaded_yaml:
            yaml_record = yaml.dump([ride])
            f.write(yaml_record)

    return returned_content

def is_browser(user_agent) -> bool:
    """
    Detect if the given user agent is a browser or not
    """
    result = re.search("Mozilla", user_agent)
    if result:
        return True
    return False

env_vars = load_env()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    """
    Get a new SEEN_CARS_FILE from GitHub if settings allow
    """
    if env_vars['github']['github_download_on_startup'] and env_vars['github']['github_enabled']:
        response = update_from_github()


@app.get('/')
async def main(request: Request, user_agent: Annotated[str | None, Header()] = None):
    """
    Show a form when / is called via get
    """
    if is_browser(user_agent):
        lines = load_lines()
        return templates.TemplateResponse(request=request, name="add_ride.j2", context={"lines": lines})
    return {"app_name": APP_NAME, "version": APP_VERSION}


@app.get('/rides')
async def get_all_rides(request: Request, user_agent: Annotated[str | None, Header()] = None):
    """
    Show the user the cars observed
    """
    rides = get_rides()
    sorted_list = sorted(rides, key=lambda x: int(x['car_no']))
    if is_browser(user_agent):
        list_expanded = []
        for ride in sorted_list:
            added_record = {"car_no": ride['car_no'], "date": ride['date'], "line": await get_line_longname(ride['line'])}
            list_expanded.append(added_record)
        return templates.TemplateResponse(request=request, name="rides.j2",
                                          context={"rides": list_expanded})
    return sorted_list


@app.get('/rides/{car_no}')
async def get_car(request: Request, user_agent: Annotated[str | None, Header()] = None, car_no = 0):
    """
    Show the user a specific car observed
    """
    seen_rides = get_rides_on_a_car(queried_car_no=car_no)
    sorted_list = sorted(seen_rides, key=lambda x: int(x['car_no']))
    if is_browser(user_agent):
        return templates.TemplateResponse(request=request, name="rides.j2",
                                          context={"rides": sorted_list})
    return sorted_list


@app.get('/lines')
async def get_lines(request: Request, user_agent: Annotated[str | None, Header()] = None):
    """
    Show the user the lines available
    """
    lines = load_lines()
    if is_browser(user_agent):
        return templates.TemplateResponse(request=request, name="lines.j2",
                                          context={"lines": lines})

    return lines

@app.post('/add_ride')
async def add_ride(request: Request, car_no: Annotated[str, Form()], line: Annotated[str, Form()],
                   user_agent: Annotated[str | None, Header()] = None):
    """
    Call to add a new ride
    """
    return_status = await add_ride_instance(car_no, line)
    if return_status:
        lines = load_lines()
        if is_browser(user_agent):
            return templates.TemplateResponse(request=request, name="add_ride.j2",
                                              context={"lines": lines,
                                                       "status": f"Added {car_no} on {await get_line_longname(line)}."})
        return {json.dumps(return_status)}
    return None


@app.get('/scrub')
# async def scrub_test_rides(request: Request):
async def scrub_test_rides(request: Request, user_agent: Annotated[str | None, Header()] = None):
    """
    Remove all ride with car_no > CAR_NO_LIMIT
    """
    valid_rides = []
    scrubbed_rides = []
    rides = get_rides()

    for ride in rides:
        if int(ride['car_no']) > CAR_NO_LIMIT:
            send_slack_msg(f"Car number {ride['car_no']} is not valid. Removing")
            scrubbed_rides.append(ride)
        else:
            valid_rides.append(ride)

    with open(SEEN_CARS_FILE, encoding="utf8", mode='w') as f:
        for ride in valid_rides:
            yaml_record = yaml.dump([ride])
            f.write(yaml_record)

    push_to_github()

    if is_browser(user_agent):
        return templates.TemplateResponse(request=request, name="scrub.j2",
                                          context={"valid_count": len(valid_rides),
                                                   "scrub_count": len(scrubbed_rides)})

    if scrubbed_rides:
        return {"message": f"Scrubbed values above {CAR_NO_LIMIT}",
                "values": scrubbed_rides}
    return {"message": "No rides scrubbed."}


@app.get('/stock')
async def stock_report(request: Request, user_agent: Annotated[str | None, Header()] = None):
    """
    Show the user a summary of the rolling stock ridden
    """
    rides = get_rides()
    stock_counts = {
        "CQ310": 0,
        "CQ311": 0,
        "CQ312": 0,
        "CQ400": 0
    }
    for ride in rides:
        if int(ride['car_no']) >= 101 and int(ride['car_no']) <= 200:
            stock_counts['CQ310'] += 1
        if int(ride['car_no']) >= 501 and int(ride['car_no']) <= 520:
            stock_counts['CQ310'] += 1
        if int(ride['car_no']) >= 201 and int(ride['car_no']) <= 320:
            stock_counts['CQ311'] += 1
        if int(ride['car_no']) >= 601 and int(ride['car_no']) <= 664:
            stock_counts['CQ312'] += 1
        if int(ride['car_no']) >= 667 and int(ride['car_no']) <= 702:
            stock_counts['CQ312'] += 1

    if is_browser(user_agent):
        listed_counts = []
        for key, value in stock_counts.items():
            listed_counts.append((key, value))
        print(f"{listed_counts=}")
        return templates.TemplateResponse(request=request, name="stock_report.j2",
                                          context={"stock_counts": listed_counts})
    return {"contents": stock_counts}

@app.get("/ping")
async def ping():
    """
    A URL to make sure this is working
    """
    return {"app_name": APP_NAME, "version": APP_VERSION}
