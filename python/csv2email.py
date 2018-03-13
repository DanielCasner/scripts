#!/usr/bin/env python3
"""
A utility to convert a contact list CSV to a list of recipients suitable for pasing into an email client.
"""
__author__ = "Daniel Casner <daniel@danielcasner.org>"

import argparse
import csv
from collections import defaultdict


def condence_recipients(contacts):
    "Condences the list of recipiends for an email if last names match"
    return {email: " and ".join((" ".join(name) for name in names)) for (email, names) in contacts.items()}


def csv2email(args):
    "Main method for program"
    email_dict = defaultdict(list)
    reader = csv.reader(args.source, delimiter=",")
    for row in reader:
        email_dict[row[args.email]].append((row[args.first], row[args.last]))
    contacts = condence_recipients(email_dict)
    return ['"{name}" <{email}>'.format(name=value, email=key) for key, value in contacts.items()]


if __name__ == '__main__':
    Parser = argparse.ArgumentParser()
    Parser.add_argument("source", type=argparse.FileType('r'), help="The source CSV file")
    Parser.add_argument("first", type=int, help="Column index of the first name")
    Parser.add_argument("last", type=int, help="Column index of the last name")
    Parser.add_argument("email", type=int, help="Column index of the email address")
    ARGS = Parser.parse_args()
    print(",\n".join(csv2email(ARGS)))
