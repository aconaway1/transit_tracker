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

- `env.yml`: The environment variables including those used by GitHub and Slack actions

```
name: Aaron's Transit Tracker
version: XXX
github:
  github_enabled: True
  github_username: <MY GITHUB USERNAME>
  github_api_token: <MY GITHUB API TOKEN>
  github_repo_name: <THE REPO WHERE THE UPDATES ARE STORED>
  github_base_url: https://api.github.com
slack:
  slack_enabled: True
  slack_incoming_webhook: <MY WEBHOOK URL>
```

See [this link](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api?apiVersion=2022-11-28) for more info about the API token.

- `linedate.yml`: A list of train lines with short and long names

This is set up for MARTA by default.

- `data/seen_cars.yml`: The rides you've taken with car number, date, and line

This is the file that will be committed to the GitHub repo by default.

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

## Utilities

### `ride_importer.py`

This is a standalone Python script to take my old CSV file (called `rides_to_import.csv`) where I was tracking my rides and put them
into the `seen_cars.yml` file.

The format of the records is

> car_no,date,car_type,line

`date` is in `%d/%m/%Y` format.

`car_type` is not used, so it's ignored for now.

`line` is the shortname of the line ("reds", "bluew", etc.)