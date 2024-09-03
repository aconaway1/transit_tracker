import yaml
import datetime

IMPORT_FILE = "rides_to_import.csv"
INPUT_DATE_FORMAT = "%m/%d/%Y"
OUTPUT_DATE_FORMAT = "%Y-%m-%d"
SEEN_CARS_FILE = "data/seen_cars.yml"

def main():

    rides_to_add = []
    with open(IMPORT_FILE, encoding="utf8") as f:
        lines = f.readlines()

    for line in lines:
        line_data = line.split(",")

        car_no = line_data[0].strip()
        imported_date = datetime.datetime.strptime(line_data[1], INPUT_DATE_FORMAT)
        date = imported_date.strftime(OUTPUT_DATE_FORMAT)
        if line_data[3].strip() == "Active":
            print(f"{line_data}")
            print("This is an old entry. Skipping.")
            continue
        line = line_data[3].strip().lower()

        rides_to_add.append({
            "car_no": car_no,
            "line": line,
            "date": date
        })


    with open(SEEN_CARS_FILE, 'a') as f:
        for ride in rides_to_add:
            yaml_record = yaml.dump([ride])
            f.write(yaml_record)

if __name__ == "__main__":
    main()