# Shove all this in a cell with %%writefile test_main.py in the collab
# Per https://christinahedges.github.io/astronomy_workflow/notebooks/2.0-testing/pytest.html

from main import parse_identifiers

def test_replace_bnf_does_nothing_if_only_new_format_present() -> None:
    test_id = {'bibliothèque_nationale_de_france': ['cb45200132d']} 
    exp_id = {'bibliothèque_nationale_de_france': ['cb45200132d']}

    result_id = parse_identifiers(test_id)
    assert result_id == exp_id

def test_replace_bnf_does_nothing_if_no_relevant_identifiers() -> None:
    test_id = {'blob': ['flop'], 'blip': ['blap']}
    exp_id = {'blob': ['flop'], 'blip': ['blap']}

    result_id = parse_identifiers(test_id)
    assert result_id == exp_id

def test_replace_bnf_works_when_there_is_only_bnf() -> None:
    test_id = {'bibliothèque_nationale_de_france_(bnf)': ['2531-1964']}
    exp_id = {'bibliothèque_nationale_de_france': ['2531-1964']}

    result_id = parse_identifiers(test_id)
    assert result_id == exp_id

def test_replace_bnf_handles_both_ids_present() -> None:
    test_id = {'bibliothèque_nationale_de_france': ['177958294', '177961376'], 'bibliothèque_nationale_de_france_(bnf)': ['177961813']}
    exp_id = {'bibliothèque_nationale_de_france': ['177958294', '177961376', '177961813']}

    result_id = parse_identifiers(test_id)
    assert result_id == exp_id

def test_replace_bnf_wont_duplicate_existing_entries() -> None:
    test_id = {'bibliothèque_nationale_de_france': ['177958294', '177961376'], 'bibliothèque_nationale_de_france_(bnf)': ['177961376']}
    exp_id = {'bibliothèque_nationale_de_france': ['177958294', '177961376']}

    result_id = parse_identifiers(test_id)
    assert result_id == exp_id

def test_replace_bnf_preserves_dict_order() -> None:
    test_id = {'another_identifier': 'some value', 'bibliothèque_nationale_de_france_(bnf)': ['2531-1964'], 'squiggle': 'wiggle'}
    exp_id = {'another_identifier': 'some value', 'bibliothèque_nationale_de_france': ['2531-1964'], 'squiggle': 'wiggle'}

    result_id = parse_identifiers(test_id)
    assert result_id == exp_id

def test_replace_bnf_collapses_list_handles_dupes_and_uniques_and_preserves_order_when_moving_bnf_into_existing_entry() -> None:
    test_id = {'bibliothèque_nationale_de_france': ['177961813'], 'another_identifier': 'some value', 'bibliothèque_nationale_de_france_(bnf)': ['177961813', '2531-1964', '177961813'], 'squiggle': 'wiggle'}
    exp_id = {'another_identifier': 'some value', 'bibliothèque_nationale_de_france': ['177961813', '2531-1964'], 'squiggle': 'wiggle'}

    result_id = parse_identifiers(test_id)
    for k, v in result_id.items():
        assert v == exp_id.get(k)
