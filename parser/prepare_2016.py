from __future__ import division
import json
import csv
import re
from collections import Counter
import sys

"""
Distribution of ID numbers
python ids.py <text file with ids>
"""

id_reg = re.compile("\d{13}")
ids = set()

party_map = {
    "AFRICAN NATIONAL CONGRESS" : "ANC",
    "UNITED CHRISTIAN DEMOCRATIC PARTY" : "UCDP",
    "ECONOMIC FREEDOM FIGHTERS" : "EFF",
    "DEMOCRATIC ALLIANCE" : "DA",
    "SOUTH AFRICAN DEMOCRATIC CONGRESS" : "SADC",
    "PAN AFRICANIST CONGRESS OF AZANIA" : "PAC",
    "UNITED DEMOCRATIC MOVEMENT" : "UDM",
    "CONGRESS OF THE PEOPLE" : "COPE",
    "AFRICAN CHRISTIAN DEMOCRATIC PARTY" : "ACDP",
    "INKATHA FREEDOM PARTY" : "IFP",
    "AZANIAN PEOPLE'S ORGANISATION" : "AZAPO",
    "ALLIANCE OF FREE DEMOCRATS" : "AFD",
    "INDEPENDENT DEMOCRATS" : "ID",
    "GREAT KONGRESS OF SOUTH AFRICA" : "GKSA",
    "VRYHEIDSFRONT PLUS" : "FF Plus",
    "UNITED INDEPENDENT FRONT" : "UIF",
    "MOVEMENT DEMOCRATIC PARTY" : "MDP",
    "AFRICAN PEOPLE'S CONVENTION" : "APC",
    "CHRISTIAN DEMOCRATIC ALLIANCE" : "CDA",
    "PAN AFRICANIST MOVEMENT" : "PAM",
    "NATIONAL DEMOCRATIC CONVENTION" : "NDC",
    "NEW VISION PARTY" : "NVP",
    "MINORITY FRONT" : "MF",
    "WOMEN FORWARD" : "Women Forward",
    "INDEPENDENT CANDIDATE" : "Independent",
    "A PARTY" : "A Party",
    "AL JAMA-AH" : "Al Jama-ah",
}


def median(lst):
    even = (0 if len(lst) % 2 else 1) + 1
    half = (len(lst) - 1) // 2
    return int(sum(sorted(lst)[half:half + even]) / float(even))

def extract_age(id):
    year2 = int(id[0:2])
    return 2016 - (year2 + 1900)
    
def extract_age_range(id):
    age = extract_age(id)
    if age < 39:
        return "less than 39"
    elif age < 60:
        return "39 - 59"
    elif age < 80:
        return "60 - 79"
    return "80 and over"

def extract_starsigns(id):
    month = int(id[2:4])
    day = int(id[4:6])
    if (month == 3 and day >= 21) or (month == 4 and day <= 19):
        return "Aries"
    elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
        return "Taurus"
    elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
        return "Gemini"
    elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
        return "Cancer"
    elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return "Leo"
    elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return "Virgo"
    elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
        return "Libra"
    elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
        return "Scorpio"
    elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
        return "Sagittarius"
    elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
        return "Capricorn"
    elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
        return "Aquarius"
    elif (month == 2 and day >= 19) or (month == 3 and day <= 20):
        return "Pisces"

def extract_gender(id):
    val = int(id[6])
    if val < 4:
        return "Female"
    return "Male"

def histogram(hash, count):
    items = hash.items()
    sorted_items = sorted(items, key=lambda x: x[1])
    perc_items = [(key, val/count * 100) for key, val in sorted_items]
    for key, val in perc_items:
        print "%s: %.2f%%" % (key, val)

def print_output(title, hist, count):
    print ""
    print title
    print "=" * 20
    print ""
    histogram(hist, count)

class Parser(object):
    NEXT = "NEXT"
    SAME = "SAME"

    def __init__(self):
        self._type = ""
        self._state = self.state_wait_for_type
        self._province = None
        self._party = None
        self._type = None
        self.data = {
            "national" : [],
            "regional" : [],
        }
        self._national = []
        self._regional = []

    def state_wait_for_type(self, line):
        if "NATIONAL LIST" in line:
            self._type = "national"
            self._state = self.state_wait_for_party
        elif "REGIONAL LIST" in line:
            self._type = "regional"
            self._state = self.state_wait_for_province
        return Parser.NEXT

    def state_wait_for_province(self, line):
        if "Province:" in line:
            (_, province) = line.split(":")
            self._province = province.strip()
            self._state = self.state_wait_for_party
        return Parser.NEXT
    
    def state_wait_for_party(self, line):
        if "Party Name:" in line:
            (_, party) = line.split(":")
            self._party = party.strip()
            self._state = self.state_wait_for_table
        return Parser.NEXT

    def reset(self):
        self._party = None
        self._province = None
        self._type = None

    def state_wait_for_table(self, line):
        def find_extent(label1, label2):
            return (line.find(label1), line.find(label2))

        if "" in line:
            self.reset()
            self._state = self.state_wait_for_type
            return Parser.SAME

        if "Party" in line and "Position" in line and "Full Name" in line:
            self._pos = [
                find_extent("Last Name", "Full Name"),
                find_extent("Full Name", "ID"),
                find_extent("ID", "AN"),
            ]

            self._state = self.state_process_candidate
        return Parser.NEXT

    def state_process_candidate(self, line):
        def extent(idx):
            e = self._pos[idx]
            return line[e[0]: e[1]]

        if "" in line:
            self.reset()
            self._state = self.state_wait_for_type
            return Parser.SAME

        if not re.findall(id_reg, line):
            # Skip lines that don't have IDs
            return Parser.NEXT
        else:
            last_name = extent(0).strip()
            first_name = extent(1).strip()
            id = extent(2).strip()
            if not id in ids: # This isn't strictly correct, depends on what you're doing with the data
                self.data[self._type].append([
                    "%s %s" % (first_name, last_name),
                    self._province or "National",
                    self._party,
                    extract_age(id),
                    extract_age_range(id),
                    extract_gender(id),
                ])
                ids.add(id)

            return Parser.NEXT

    def parse(self, line):
        while True:

            result = self._state(line)
            if result == parser.SAME:
                continue
            break

def extract_unique_ids(lst):
    return set(x["IDNumber"] for x in lst)

def party_output(data):
    results = []
    parties = set(el["Party"] for el in data)

    def extract_details(x):
        return [
            x["Fullname"] + " " + x["Surname"],
            x["Province"],
            extract_age(x["IDNumber"]),
            extract_gender(x["IDNumber"])
        ]

    for party in parties:
        candidates = [x for x in data if x["Party"] == party]
        if len(extract_unique_ids(candidates)) < 50:
            continue
        dict_by_id = { x["IDNumber"] : x for x in candidates }
        unique_ids = sorted(extract_unique_ids(candidates))
        youngest = [extract_details(dict_by_id[x]) for x in unique_ids[-5::]]
        oldest = [extract_details(dict_by_id[x]) for x in unique_ids[0:5]]
        results.append({
            "party" : party,
            "abbr" : party_map.get(party, ""),
            "males" : len([x for x in unique_ids if extract_gender(x) == "Male"]),
            "females" : len([x for x in unique_ids if extract_gender(x) == "Female"]),
            "young" : len([x for x in unique_ids if extract_age_range(x) == "less than 39"]),
            "middle" : len([x for x in unique_ids if extract_age_range(x) == "39 - 59"]),
            "old" : len([x for x in unique_ids if extract_age_range(x) == "60 - 79"]),
            "vold" : len([x for x in unique_ids if extract_age_range(x) == "80 and over"]),
            "youngest" : youngest,
            "oldest" : oldest,
            "median_age" : median([extract_age(x) for x in unique_ids])
        })
    return results

if __name__ == "__main__":
    data = list(csv.DictReader(open("candidates_2016.csv")))
    results = party_output(data)

    f = open("parties_2016.json", "w")
    f.write(json.dumps(results, indent=4))
    f.close()
