"""
A web interface to track MARTA car rides
"""
from datetime import datetime
from typing import Annotated
import yaml
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import psycopg2

ENV_FILE = "env.yml"

def get_cars():
    """
    Query the DB for the cars observed
    """
    db_conn = psycopg2.connect(
        host="db",
        database="ttu",
        user=env_vars['db_user'],
        password=env_vars['db_pass']
    )
    cur = db_conn.cursor()
    cur.execute("select * from observed_cars")
    results = cur.fetchall()
    db_conn.close()
    return results

def get_a_car(car_no: int):
    """
    Query the DB for a specific car
    """
    db_conn = psycopg2.connect(
        host="db",
        database="ttu",
        user=env_vars['db_user'],
        password=env_vars['db_pass']
    )
    cur = db_conn.cursor()
    cur.execute(f"select * from observed_cars where car_no = {car_no}")
    results = cur.fetchall()
    db_conn.close()
    return results

def load_lines():
    """
    Load the train lines from the DB
    """
    db_conn = psycopg2.connect(
        host="db",
        database="ttu",
        user=env_vars['db_user'],
        password=env_vars['db_pass']
    )
    cur = db_conn.cursor()
    cur.execute("select * from lines")
    results = cur.fetchall()
    db_conn.close()
    return results

def load_env():
    """
    Load the environment
    """
    with open(ENV_FILE, encoding="utf8") as file:
        return yaml.safe_load(file)


env_vars = load_env()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get('/', response_class=HTMLResponse)
async def main(request: Request):
    """
    Show a form when / is called via get
    """
    lines = load_lines()
    return templates.TemplateResponse(request=request, name="add_car.j2", context={"lines": lines})

@app.post('/add_car')
async def add_car(car_no: Annotated[str, Form()], line: Annotated[str, Form()]):
    """
    Add a car observation to the DB
    """
    today = datetime.now().strftime("%Y-%m-%d")
    sql = 'INSERT INTO observed_cars (car_no, line, observation_date) VALUES (%s, %s, %s)'
    val = (car_no, line, today)
    db_conn = psycopg2.connect(
        host="db",
        database="ttu",
        user=env_vars['db_user'],
        password=env_vars['db_pass']
    )
    cur = db_conn.cursor()
    cur.execute(sql, val)
    db_conn.commit()
    db_conn.close()
    return HTMLResponse(f"You observed car {car_no} on line {line} on {today}.")


@app.get('/cars')
async def get_all_cars():
    """
    Show the user the cars observed
    """
    parsed_cars = []
    observations = get_cars()
    lines = load_lines()
    friendly_lines = {}
    for line in lines:
        friendly_lines[line[0]] = line[2]
    for obs in observations:
        parsed_cars.append({
            "car_no": obs[0],
            "line": friendly_lines[obs[1]],
            "date_obs": obs[2]
        })
    return parsed_cars


@app.get('/cars/{car_no}')
async def get_car(car_no):
    """
    Show the user a specific car observed
    """
    return get_a_car(car_no=car_no)


@app.get('/lines')
async def get_lines():
    """
    Show the user the lines available in the DB
    """
    return load_lines()
