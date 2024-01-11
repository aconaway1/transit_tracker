import yaml
from typing import Annotated
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import date

ENV_FILE = "env.yml"

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

class Car(BaseModel):
    
    car_no: int | None
    date_seen: str | None
    line: str | None
    
    def set_car_no(self, car_no):
        self.car_no = car_no
        
    def set_date_seen(self, date_seen):
        self.date_seen = date_seen
        
    def set_line(self, line):
        self.line = line

def load_env():
    with open(ENV_FILE) as file:
        return yaml.safe_load(file)
    
    
def load_static_page(filename):
    full_file_name = f"static/{filename}"
    print(full_file_name)
    f = open(f"static/{filename}", "r")
    lines = f.readlines()
    return HTMLResponse(content=lines, status_code=200)
    
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get('/', response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse(request=request, name="add_car.j2")

@app.post('/add_car')
async def add_car(car_no: Annotated[str, Form()], line: Annotated[str, Form()]):
    if line not in VALID_LINES:
        return(f"{line} is not a valid line. Needs to be one of {VALID_LINES}")
    
    try:
        if not isinstance(int(car_no), int):
            return(f"The car number {car_no} is not an integer.")
    except ValueError:
        return(f"{car_no} is not a valid car number.")
    
    
    obs_date = date.today()
    
    return HTMLResponse(f"You observed car {car_no} on line {line} on {obs_date}.")
    