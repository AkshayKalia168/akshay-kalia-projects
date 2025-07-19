#Author: Akshay Kalia
import csv
import sys
def main():
    records = []
    if len(sys.argv) > 3:
        sys.exit("Too many command-line arguments")
    elif len(sys.argv) < 3:
        sys.exit("Too few command-line arguments")
    inputfile = sys.argv[1]
    outputfile = sys.argv[2]
    try:
        with open(f"{inputfile}", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                last, first = row["name"].split(", ")
                department = row["department"]
                records.append({"first": first, "last": last, "department": department})
    except(FileNotFoundError):
        sys.exit(f"Could not read {inputfile}")
    with open(f"{outputfile}", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["first", "last", "department"])
        writer.writeheader()
        for row in lists:
            writer.writerow(row)
main()











