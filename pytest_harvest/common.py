def get_fixture_value(request, fixture_name):
    """
    Returns the value associated with fixture named `fixture_name`, in provided request context.
    This is just an easy way to use `getfixturevalue` or `getfuncargvalue` according to whichever is availabl in
    current pytest version

    :param request:
    :param fixture_name:
    :return:
    """
    try:
        # Pytest 4+ or latest 3.x (to avoid the deprecated warning)
        return request.getfixturevalue(fixture_name)
    except AttributeError:
        # Pytest 3-
        return request.getfuncargvalue(fixture_name)
