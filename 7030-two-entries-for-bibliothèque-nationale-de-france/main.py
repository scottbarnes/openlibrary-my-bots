from __future__ import annotations

import copy
import os
from collections import namedtuple
from dataclasses import dataclass
from typing import Final

import requests
from olclient.openlibrary import OpenLibrary

# Query from Grand Master D: https://github.com/internetarchive/openlibrary/issues/7030
QUERY: Final = "https://openlibrary.org/query.json?type=/type/edition&identifiers.biblioth%C3%A8que_nationale_de_france_(bnf)~=*&limit=500"
DEPRECIATED_NAME: Final = "bibliothèque_nationale_de_france_(bnf)"
NEW_NAME: Final = "bibliothèque_nationale_de_france"


@dataclass
class BnfEdition:
    olid: str
    processed: bool = False
    already_updated: bool = False


def get_ol_connection(
    user: str, password: str, base_url: str = "https://openlibrary.org"
) -> OpenLibrary:
    C = namedtuple("Credentials", ["username", "password"])
    credentials = C(user, password)
    return OpenLibrary(base_url=base_url, credentials=credentials)


def get_editions_to_update() -> list[BnfEdition]:
    """
    Gets a list of dicts in the form [{'key': '/books/OL20422410M'}, {'key': '/books/OL25438374M'}, ...],
    and returns:
        [BnfEdition(olid='OL20422410M', processed=False, already_updated=False), ...]
    """
    r = requests.get(QUERY)
    edition_keys = r.json()
    # {'key': '/books/OL20422410M'} -> 'OL20422410M'
    get_id = lambda k: k.get("key").split("/")[-1]
    edition_ids = (get_id(edition) for edition in edition_keys)

    # Converting to BnfEdition in an extra step for code clarity.
    return [BnfEdition(olid=edition_id) for edition_id in edition_ids]


def parse_identifiers(ids: dict[str, list[str]]) -> dict[str, list[str]]:
    """
    Convert bibliothèque_nationale_de_france_(bnf) to bibliothèque_nationale_de_france
    within an identifier. If bibliothèque_nationale_de_france already exists, append
    the _(bnf) value to the existing version. This won't duplicate any entries, and
    it will preserve the dictionary order.
    """
    identifiers = copy.deepcopy(ids)
    KEYS = identifiers.keys()

    # Handle only DEPRECIATED_NAME in the identifier.
    if DEPRECIATED_NAME in KEYS and NEW_NAME not in KEYS:
        return {
            NEW_NAME if k == DEPRECIATED_NAME else k: v for k, v in identifiers.items()
        }

    # Handle DEPRECIATED_NAME not present
    if DEPRECIATED_NAME not in KEYS:
        return identifiers

    # Handle both DEPRECIATED_NAME and NEW_NAME present.
    values_from_depreciated_name = identifiers.pop(DEPRECIATED_NAME, None)
    if values_from_depreciated_name is None:
        raise ValueError("expected DEPRECIATED_NAME as a key but it wasn't there")

    for value in values_from_depreciated_name:
        # Don't duplicate existing entries.
        if value in identifiers[NEW_NAME]:
            continue

        identifiers[NEW_NAME].append(value)

    return identifiers


def main(bnf_editions: list[BnfEdition]) -> None:
    ## Remove the following in the collab
    # Set in .env and load into the env via the shell, or docker-compose if using that.
    BOT_USER = os.environ["bot_user"]
    BOT_PASSWORD = os.environ["bot_password"]
    ol = get_ol_connection(
        user=BOT_USER, password=BOT_PASSWORD, base_url="http://localhost:8080"
    )
    ### END REMOVE ###

    for bnf_edition in bnf_editions:
        edition = ol.get(bnf_edition.olid)
        if edition is None:
            print(f"Skipping {bnf_edition.olid}: not found")
            continue

        existing_identifiers = copy.deepcopy(edition.identifiers)
        new_identifiers = parse_identifiers(existing_identifiers)

        # Stop if nothing has changed.
        if existing_identifiers == new_identifiers:
            bnf_edition.already_updated = True
            print(f"Not updating: {bnf_edition.olid}")
            continue

        bnf_edition.processed = True

        edition.identifiers = new_identifiers
        edition.save(comment=f"changing {DEPRECIATED_NAME} to {NEW_NAME} (#7030)")
        print(f"Updated {bnf_edition.olid}")

    updated_editions = [
        edition for edition in bnf_editions if edition.already_updated is False
    ]
    not_updated_editions = [
        edition for edition in bnf_editions if edition.already_updated is True
    ]

    print("\nProcess complete")
    print(f"Number updated: {len(updated_editions)}")
    print(f"Already updated: {['/books/' + e.olid for e in not_updated_editions]}")
    print(f"Total: {len(updated_editions) + len(not_updated_editions)}")


# Not necessary in collab. Just execute `main()` in its own cell.
if __name__ == "__main__":
    # bnf_editions = get_editions_to_update()
    bnf_editions = [BnfEdition(olid="OL24726145M")]
    main(bnf_editions)
