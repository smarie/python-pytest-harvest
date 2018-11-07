from collections import OrderedDict


PYTEST_OBJ_NAME = 'pytest_obj'


def get_session_synthesis_dct(session):

    res_dct = OrderedDict()
    for item in session.items:
        item_dct = OrderedDict()

        # Fill the dictionary with information about this test node
        # -- test object
        item_dct[PYTEST_OBJ_NAME] = item.obj

        # -- parameters & fixtures
        for param_name in item.fixturenames:
            if param_name in item.callspec.params:
                # this is a param: ok
                item_dct[param_name] = item.callspec.params[param_name]
            else:
                # this is a fixture: it is not saved, this is normal (hence the storage decorator)
                pass

        # For info: https://docs.pytest.org/en/latest/_modules/_pytest/runner.html
        # used_fixtures = sorted(item._fixtureinfo.name2fixturedefs.keys())
        # if used_fixtures:
        #     tw.write(" (fixtures used: {})".format(", ".join(used_fixtures)))

        res_dct[item.nodeid] = item_dct

    return res_dct
