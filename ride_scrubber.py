import yaml
import datetime

SEEN_CARS_FILE = "data/seen_cars.yml"
CAR_NO_LIMIT = 9999
def main():

    valid_rides = []

    with open(SEEN_CARS_FILE, encoding="utf8") as f:
        rides = yaml.safe_load(f)

    for ride in rides:
        if int(ride['car_no']) > CAR_NO_LIMIT:
            print(f"Car number {ride['car_no']} is not valid. Skipping.")
            continue
        else:
            valid_rides.append(ride)

    with open(SEEN_CARS_FILE, encoding="utf8", mode='w') as f:
        for ride in valid_rides:
            yaml_record = yaml.dump([ride])
            f.write(yaml_record)

if __name__ == "__main__":
    main()