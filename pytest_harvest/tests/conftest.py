pytest_plugins = ["pytester"]
# In order to run meta-tests, see https://docs.pytest.org/en/latest/writing_plugins.html
#
# IMPORTANT: the pytester plugin hangs instead of failing on windows, so a bug is hard to debug. The linux
# version does not, so a run on the travis CI usually helps.
