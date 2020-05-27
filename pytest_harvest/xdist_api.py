# from distutils.version import LooseVersion

try:
    from xdist import __version__ as xdist_version
except ImportError:
    # no xdist installed - create a substitute API
    def _is_xdist_worker(session):
        return False

    def _is_xdist_master(session):
        return False

    def is_main_process(session):
        return True

    def get_xdist_worker_id(request_or_session):
        return "master"  # for consistency with the original method
else:
    # if LooseVersion(xdist_version) <= LooseVersion("1.31.0"):
    # old xdist with no api
    def _is_xdist_worker(request_or_session):
        """Return `True` if this is a xdist worker, `False` otherwise

        :param request_or_session: the `pytest` `request` or `session` object
        :return:
        """
        return hasattr(request_or_session.config, "workerinput")

    def _is_xdist_master(request_or_session):
        """Return `True` if this is the xdist master, `False` otherwise

        Note: this method returns `False` when distribution has not been activated
        at all.

        :param request_or_session: the `pytest` `request` or `session` object
        :return:
        """
        return (not _is_xdist_worker(request_or_session)
                and getattr(request_or_session.config.option, 'dist', 'no') != "no")

    def get_xdist_worker_id(request_or_session):
        """Return the id of the current worker ('gw0', 'gw1', etc) or None
        if running on the master node.

        :param request_or_session: the `pytest` `request` or `session` object
        :return:
        """
        if hasattr(request_or_session.config, "workerinput"):
            return request_or_session.config.workerinput["workerid"]
        else:
            # TODO shall we raise an exception if dist is not enabled ?
            #  i.e. `not is_xdist_master(request_or_session)` ?
            return "master"
    # else:
    #     from xdist import (get_xdist_worker_id as get_xdist_worker_id,
    #                        is_xdist_master as _is_xdist_master,
    #                        is_xdist_worker as _is_xdist_worker)

    def is_main_process(session):
        return not _is_xdist_worker(session)
