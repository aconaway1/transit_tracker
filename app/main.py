import yaml
from typing import Annotated
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
import operator
import psycopg2

ENV_FILE = "env.yml"
OBSERVED_CARS_FILE = "observed_cars.yml"

VALID_LINES = [
    "redn",
    "reds",
    "goldn",
    "golds",
    "bluee",
    "bluew",
    "greene",
    "greenw"
]


def get_cars():
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
    with open(ENV_FILE) as file:
        return yaml.safe_load(file)
    
env_vars = load_env()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get('/', response_class=HTMLResponse)
async def main(request: Request):
    lines = load_lines()
    return templates.TemplateResponse(request=request, name="add_car.j2", context={"lines": lines})

@app.post('/add_car')
async def add_car(car_no: Annotated[str, Form()], line: Annotated[str, Form()]):
    written_record = {}
    written_record['car_no'] = car_no
    written_record['line'] = line
    written_record['obs_date'] = datetime.now().strftime("%Y-%m-%d")
    
    sql = f'INSERT INTO observed_cars (car_no, line, observation_date) VALUES (%s, %s, %s)'
    val = (written_record['car_no'], written_record['line'], written_record['obs_date'])
    
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
     
    
    return HTMLResponse(f"You observed car {written_record['car_no']} on line {written_record['line']} on {written_record['obs_date']}.")


@app.get('/cars')
async def get_all_cars(request: Request):
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
    return get_a_car(car_no=car_no)


@app.get('/lines')
async def get_lines():
    return load_lines()