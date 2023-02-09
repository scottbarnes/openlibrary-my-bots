import json
import os
import requests

from typing import Any, Final
from collections import namedtuple
from olclient import OpenLibrary, config

# Set in .env and load into the env via the shell, or docker-compose if using that.
ACCESS_KEY = os.environ["ol_access_key"]
SECRET_KEY = os.environ["ol_secret_key"]

# Settings for testing in the local developer environment

# BASE_URL = "http://localhost:8080"
# BOT_USER = os.environ["bot_user"]
# BOT_PASSWORD = os.environ["bot_password"]
# ISBN_QUERY: Final = "http://localhost:8080/query.json?type=/type/edition&isbn~=*&limit=500"
# PUBLISHER_QUERY: Final = "http://localhost:8080/query.json?type=/type/edition&publisher~=*&limit=500"
# GET_PUT_URL: Final = "http://localhost:8080/books/%s.json"

GET_PUT_URL: Final = "https://openlibrary.org/books/%s.json"
ISBN_QUERY: Final = (
    "https://openlibrary.org/query.json?type=/type/edition&isbn~=*&limit=500"
)
PUBLISHER_QUERY: Final = (
    "https://openlibrary.org/query.json?type=/type/edition&publisher~=*&limit=500"
)


class NotIsbnError(Exception):
    """Number is not a valid ISBN 10 or ISBN 13"""

    pass


class HasExistingISBN10or13Error(Exception):
    """
    Edition has existing ISBN 10 or 13. The current script doesn't handle that,
    but it would be good to know if the exist and it should handle that.
    """


def get_ol_connection(
    user: str, password: str, base_url: str = "https://openlibrary.org"
) -> OpenLibrary:
    C = namedtuple("Credentials", ["username", "password"])
    credentials = C(user, password)
    return OpenLibrary(base_url=base_url, credentials=credentials)


def get_editions_to_update(query: str) -> list[str]:
    """
    Gets a list of dicts in the form [{'key': '/books/OL20422410M'}, {'key': '/books/OL25438374M'}, ...],
    and returns:
        ["OL123M", "OL456M", ...]
    """
    r = requests.get(query)
    edition_keys = r.json()
    # edition_keys = r.json()[:5]
    # {'key': '/books/OL20422410M'} -> 'OL20422410M'
    get_id = lambda k: k.get("key").split("/")[-1]
    edition_ids = [get_id(edition) for edition in edition_keys]

    return edition_ids


def get_isbn_10_and_13(isbns: list[str]) -> tuple[list[str], list[str]]:
    """
    Take a list[str] of ISBNs and return a tuple with a list of:
        ISBN 10s, and
        ISBN 13s.
    E.g.:
        >>> get_isbn_10_and_13(["0002217317"])
        ("0002217317", [])
        >>> get_isbn_10_and_13("0002217317", "0030050456", "9780002217316", "9780030050459")
        (["0002217317", "0030050456"], ["9780002217316", "9780030050459"])
    """
    isbn_10s = []
    isbn_13s = []

    for isbn in isbns:
        match len(isbn):
            case 10:
                isbn_10s.append(isbn)
            case 13:
                isbn_13s.append(isbn)
            case _:
                raise NotIsbnError

    return (isbn_10s, isbn_13s)


# `edition` is olclient.openlibrary.OpenLibrary.Edition.<locals>.Edition.
def update_isbn_10_and_13(edition) -> Any:
    """
    Move ISBN values from `.isbn` if they are there to their
    respective `.isbn_10` and `.isbn_13` fields.
    """
    if not edition.get("isbn", None):
        return edition

    isbn_field = edition.get("isbn")
    print(f"isbn_field is: {isbn_field}")

    isbn_10s, isbn_13s = get_isbn_10_and_13(isbn_field)

    # Handle ISBN 10s, appending without duplicating, or creating the field if necessary.
    if edition.get("isbn_10") and isbn_10s:
        for isbn in isbn_10s:
            edition["isbn_10"].append(isbn) if isbn not in edition["isbn_10"] else None
    elif isbn_10s:
        edition["isbn_10"] = isbn_10s

    # Handle ISBN 13s, appending without duplicating, or creating the field if necessary.
    if edition.get("isbn_13") and isbn_13s:
        for isbn in isbn_13s:
            edition["isbn_13"].append(isbn) if isbn not in edition["isbn_13"] else None
    elif isbn_13s:
        edition["isbn_13"] = isbn_13s

    del edition["isbn"]

    return edition


# `edition` is olclient.openlibrary.OpenLibrary.Edition.<locals>.Edition.
def update_publishers(edition) -> Any:
    """
    Takes the list[str] from `.publisher` and append it to the
    list[str] `.publishers`, or use that value from `.publisher`
    to create `.publishers`. Returns the updated edition.
    """
    if not edition.get("publisher", None):
        return edition

    publisher = edition.get("publisher")

    if publishers := edition.get("publishers", None):
        publishers.append(publisher) if publisher not in publishers else None
    else:
        edition["publishers"] = [publisher]

    del edition["publisher"]

    return edition


def main() -> None:
    """Inoke the rest of the functions."""
    # For testing locally.
    # ol = get_ol_connection(user=BOT_USER, password=BOT_PASSWORD, base_url=BASE_URL)

    # For the live environment.
    ol = OpenLibrary(credentials=config.Credentials(access=ACCESS_KEY, secret=SECRET_KEY))

    # isbn_editions = []
    # publisher_editions = []
    isbn_editions = get_editions_to_update(ISBN_QUERY)
    publisher_editions = get_editions_to_update(PUBLISHER_QUERY)
    edition_keys = isbn_editions + publisher_editions

    for edition_key in edition_keys:
        # edition = ol.Edition.get(edition_key)
        r = ol.session.get(GET_PUT_URL % edition_key)
        edition = r.json()
        print(f"Processing {edition_key}")

        if not edition:
            continue

        edition = update_isbn_10_and_13(edition)
        edition = update_publishers(edition)

        body = edition
        body["_comment"] = "Repairing incorrect publisher and isbn fields (#7448)"

        j = json.dumps(body)

        ol.session.put(GET_PUT_URL % edition_key, j)


if __name__ == "__main__":
    main()
