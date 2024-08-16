# Transit Tracker

I started riding MARTA for fun (don't ask!) and wanted to track what cars I've
ridden. I've got a spreadsheet, but that's pretty cumbersome when I'm trying
to get on and off the train. I fired off this Python app that presents a very
simple form that I can use to record my rides.

I run this one my home machine and connect in via ZeroTier to access it. Works like a champ!

# Usage

To start it up: `docker compose up -d`

This will build a new Python image based on the `Dockerfile` directives. It will then bring up
the container with local port `8000` bound to container port `8000`. It will also
mount the `data` folder to the container so the observed cars are seen between
runs of the app.

# The Details

This thing uses FastAPI to provide an interface for a YAML file. There is no need for any
efficiency measures here since the user will only interact with it once every few hours on
average. There's some Jinja in there to make it look consistent.

## The API

See `/redoc` for more details.

## YAML Data

- `env.yml`: The environment variables; does nothing at the moment
- `linedate.yml`: A list of train lines with short and long names
- `data/seen_cars.yml`: The rides you've taken with car number, date, and line

## Templates

- `add_ride.j2`: The output from submitting a ride

## Docker Files

`Dockerfile` is used to build a Python 3.9 container and run uvicorn.

`docker-compose.yml` is used to start up the Python container, mount a data directory, and set
up the ports.

### `data` Directory

This is where the `seen_cars.yml` file lives. This is mounted on the container to share
that data between the container and host. Its primary purpose, though, is to provide 
persistence between container runs.