# Transit Tracker

First and foremost, I am a network engineer and not a developer. This is terrible code. Absolutely terrible.
Don't expect too much here.

I started riding MARTA for fun (don't ask!) and wanted to track what cars I've
ridden. I've got a spreadsheet, but that's pretty cumbersome when I'm trying
to get on and off the train. I fired off this Python app that presents a very
simple form that I can use to record my rides.

I run this one my home machine and connect in via ZeroTier to access it. Works like a champ!

# Usage

The `docker-compose.yml` file is set up to look for an image `transit_tracker` with a tag of `latest`. You'll
initially have to build this yourself using the `Dockerfile`.

> docker build -t transit_tracker:latest .

This will build a new Python image based on the `Dockerfile` directives. It will then bring up
the container with local port `8000` bound to container port `8000`. It will also
mount the `data` folder to the container so the observed cars are seen between
runs of the app.

*The process of building a container with Docker is outside the scope of this document, but there
are plenty of resources that can help. If you can't get it running, let me know, and I'll see what I can do.*

When the image is built, you can turn up the container by running this.

> docker compose up -d

Point your browser at `http://localhost:8000` to see if a form comes up.

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

## Templates

- `add_ride.j2`: The output from submitting a ride
- `toot.j2`: The format of the Mastodon update
- `footer.j2`: The same footer for every page shown
- `ride_report.j2`: The format for the ride report

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
- User-Agent checking to return HTML or JSON appropriately
- Better look of the GUI
- Instructions on running it remotely with some semblance of security
