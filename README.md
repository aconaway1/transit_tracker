# Transit Tracker

First and foremost, I am a network engineer and not a developer. This is terrible code. Absolutely terrible.
Don't expect too much here.

I started riding MARTA for fun (don't ask!) and wanted to track what cars I've
ridden. I've got a spreadsheet, but that's pretty cumbersome when I'm trying
to get on and off the train. I fired off this Python app that presents a very
simple form that I can use to record my rides.

I run this one my home machine and connect in via ZeroTier to access it. Works like a champ!

# Installation

## Requirements

This app run on Docker to make things easier. This means that you don't have to manage the modules, the packages,
or anything. You just have to make sure Docker is working. As of today (September 2024), I'm running this successfully
on Docker Desktop 4.32.0 on my laptop and Docker 24.0.7 with Docker Compose 2.3.3 on my Ubuntu nodes in the cloud.

Just a note here - `docker-compose` and `docker compose` are different things. You'll need Docker Compose version 2
to get this working.

Git is also required here. I don't think the version is important, but, as soon as I type this, something will come up.
LOL

## Setup

Clone the repo by going to your working directory (where you want the app to run) by typing this.

> git clone https://github.com/aconaway1/transit_tracker.git

This will download the repo into your current directory in a folder called `transit_tracker`. Basic Git stuff here.

A very important file is missing, though. [The `env.yml` file](#yaml-data) contains most of the configuration info, so
create one of those using proper data and put it in the `app/` folder inside the repo.

The whole thing is set up to look for an image `transit_tracker` with a tag of `latest` in your Docker image list.
You'll initially have to build this yourself using the `Dockerfile`. From the `transit-tracker` directory, run this.

> docker build -t transit_tracker:latest .

This will build a new Python container image based on the `Dockerfile` directives. It might take a few minutes initially as
it downloads the images and put them in the image list.

## Running

Bring up the app by running this command from the `transit_tracker` directory.

> docker compose up -d

This will bring up the container with local port `8000` bound to container port `8000`. It will also
mount the `data` folder to the container so the observed cars are seen between runs of the app.

Point your browser at `http://localhost:8000` to see if a form comes up.

## Stopping

From the `transit_tracker` directory, type this to stop it.

> docker compose down

# The Details

This thing uses FastAPI to provide an interface for a YAML file. There is no need for any
efficiency measures here since the user will only interact with it once every few hours on
average. There's some Jinja in there to make it look consistent.

Then initial settings are based off the MARTA train system in Atlanta. The rail lines included
are base on the Red, Gold, Green, and Blue Lines along with the Streetcar. Car numbers are assumed
to be from 100 to just over 1000 since that's how MARTA is set up.

## The API

Once this thing is up and running, see `/redoc` for more details.

## Features

* **Support for GitHub syncing**: You can have your ride data synced up to a GitHub repo.
* **Slack updates**: Update a Slack channel every time you ride.
* **Support for Mastodon updates**: You can update your friends every time you get on a train.
* **Testing car number ranges**: Any car number submitted over `CAR_NO_LIMIT` (default: 9999) will 
be mostly ignored or marked as testing.
* **Testing data scrubbing**: Any test car in the system can be removed with a click.
* **Reporting**: Some reports for all your rides and the number of each type of car you're one

## YAML Data

- `linedate.yml`: A list of train lines with short and long names

This is set up for MARTA by default - Red, Gold, Blue, and Green with directions along with the Streetcar.

- `data/seen_cars.yml`: The rides you've taken with car number, date, and line

This is the file that will be copied to the GitHub repo by default.

- `env.yml`: The environment variables including those used by GitHub, Slack, and Mastodon

```
github:
  github_enabled: True
  github_username: <MY GITHUB USERNAME>
  github_api_token: <MY GITHUB API TOKEN>
  github_repo_name: <THE REPO WHERE THE UPDATES ARE STORED>
  github_base_url: https://api.github.com
slack:
  slack_enabled: True
  slack_incoming_webhook: <MY WEBHOOK URL>
mastodon:
  mastodon_enabled: True
  mastodon_base_url: "<URL TO MASTODON INSTANCE>"
  mastodon_token: "<MASTODON APP TOKEN>"
logging:
  logging_enabled: True
  log_level: 10
  log_file: "transit.log"
  log_file_mode: "w"
  log_format: "%(asctime)s - %(levelname)s - %(message)s"
```
This file has sensitive information in it, so it's not part of the repo. You're going to have to generate the file
yourself and put it in the `app` folder.

### GitHub Config

The `github` section sets up the GitHub repos where you're storing your data. This is not the repo for this code.

If you don't want to use GitHub, then set `github_enable` to `False`.

If you don't want to download a fresh copy of your data at server startup, set `github_download_on_startup` to `False`.

`github_username` is your GitHub username.

`github_api_token` is your personal access token for your storage repo. See [this link](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api?apiVersion=2022-11-28) for more info about 
how to get that working.

`github_repo_name` is your repo where you want to store the data.

`github_base_url` is where GitHub lives. Don't change this unless GitHub told you to do so.

### Slack Config

The `slack` section is for setting up Slack notifications.

If you don't want to notify a Slack channel for changes, set `slack_enabled` to `False`.

`slack_incoming_webhook` is the URL given by Slack for notifing your channel. You can check out [this link](https://api.slack.com/messaging/webhooks) on
how to set that up.

### Mastodon Config

The `mastodon` section is for posting updates to Mastodon.

If you don't want to post to Mastodon, set `mastodon_enabled` to `False`.

`mastodon_base_url` is the base URL of your Mastodon instance. It's usually just `https://<YOUR INSTANCE>`.
  
`mastodon_token` is the app key that you set up for API calls to Mastodon. See [this link](https://docs.joinmastodon.org/client/intro/) 
as a "getting started" point. In summary, while in your Mastodon account, go to `Preferences > Development` and
add an application.

### Logging Config

**NOTE**: The implementation of logging here is terrible. It's just like "turn on logging and send some stuff." This
means you'll see some logs from other modules - particularly `requests` that is used to talk to Slack, GitHub, etc.
It's not too many messages, but this definitely needs to be fixed with a custom logger at some point.

The `logging` section is for setting up logging to file. Do a search on `python logging` if you want to tweak this.

If you don't want to enable logging, set `logging_enabled` to `False`.

The `log_level` is the value the Python `logging` module will use. The module wants a built-in value, but those
just map to integers. Debug is 10.

The `log_file` is...you guessed it! This file is in the `/code/data` folder on the containers so that the host OS
can read it.

The `log_file_mode` is the file mode. It's set to `w` here to overwrite. You could set it to `a` to append if you want
to keep the logs across container instance starts.

The `log_format` is how the log message will appear in the file. By default, we have a date & time, the logging level,
and the message. This should be good enough for like 99% of uses.

## Templates

- `add_ride.j2`: The HTML template from submitting a ride
- `toot.j2`: The format of the Mastodon update
- `footer.j2`: The same footer for every page shown
- `ride_report.j2`: The HTML template for the ride report
- `stock_report.j2`: The HTML template for the stock report
- `scrub.j2`: The HTML template for the scrub reply
- `lines.j2`: The HTML template for the line report

## Docker Files

`Dockerfile` is used to build a Python 3.10 container and run uvicorn.

`docker-compose.yml` is used to start up the Python container, mount a data directory, and set
up the ports.

### `data` Directory

This is where the `seen_cars.yml` file lives. This is mounted on the container to share
that data between the container and host. 

# Utilities

## `tests/test_main.py`

Runs a bunch of queries against the API to make sure everything is running correctly. If we don't get a `200` back,
the tests will fail. I wrote this as a quick test when new versions were published, but it can be used to make sure
any new instance is working.

> python -m unittest main/test_main.py

# TODO

There's a **LOT** to do still.

- Actually check some input for once in your life!
- Make sure remote connections (GitHub, Slack, Mastodon) actually work
- Better look of the GUI
- Instructions on running it remotely with some semblance of security
