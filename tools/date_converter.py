"""
This script takes the spreadsheet-generated date fields as `MM/DD/YYYY` and converts them to the "standard"
format of `YYYY-MM-DD`
"""
import datetime
import yaml

SOURCE_FORMAT = "%m/%d/%Y"
DESTINATION_FORMAT = "%Y-%m-%d"
SEEN_CARS_FILE = "data/seen_cars.yml"

def convert_date(date_to_convert: str) -> datetime:
    """
    Takes a date string in as SOURCE_FORMAT and returns it in DESTINATION_FORMAT
    """
    try:
        imp_datetime = datetime.datetime.strptime(date_to_convert, SOURCE_FORMAT).strftime(DESTINATION_FORMAT)
    except ValueError:
        return date_to_convert
    return imp_datetime



def main():
    """
    Main
    """
    with open(SEEN_CARS_FILE, encoding="utf8") as file:
        rides = yaml.safe_load(file)

    with open(SEEN_CARS_FILE, encoding="utf8", mode='w') as f:
        for ride in rides:
            ride['date'] = convert_date(ride['date'])
            yaml_record = yaml.dump([ride])
            f.write(yaml_record)


if __name__ == "__main__":
    main()
