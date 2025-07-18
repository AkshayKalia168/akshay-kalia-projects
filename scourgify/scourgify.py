#Author: Akshay Kalia
import csv
import sys
def main():
    lists = []
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
                house = row["house"]
                lists.append({"first": first, "last": last, "house": house})
    except(FileNotFoundError):
        sys.exit(f"Could not read {inputfile}")
    with open(f"{outputfile}", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["first", "last", "house"])
        writer.writeheader()
        for row in lists:
            writer.writerow(row)
main()











