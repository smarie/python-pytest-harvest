"""
To understand this project's build structure

 - This project uses setuptools, so it is declared as the build system in the pyproject.toml file
 - We use as much as possible `setup.cfg` to store the information so that it can be read by other tools such as `tox`
   and `nox`. So `setup.py` contains **almost nothing** (see below)
   This philosophy was found after trying all other possible combinations in other projects :)
   A reference project that was inspiring to make this move : https://github.com/Kinto/kinto/blob/master/setup.cfg

See also:
  https://setuptools.readthedocs.io/en/latest/setuptools.html#configuring-setup-using-setup-cfg-files
  https://packaging.python.org/en/latest/distributing.html
  https://github.com/pypa/sampleproject
"""
from setuptools import setup


# (1) check required versions (from https://medium.com/@daveshawley/safely-using-setup-cfg-for-metadata-1babbe54c108)
import pkg_resources

pkg_resources.require("setuptools>=39.2")
pkg_resources.require("setuptools_scm")


# (2) Generate download url using git version
from setuptools_scm import get_version  # noqa: E402

URL = "https://github.com/smarie/python-pytest-harvest"
DOWNLOAD_URL = URL + "/tarball/" + get_version()


# Setuptools_scm target version file to generate
args = {
    "write_to": "src/pytest_harvest/_version.py",
}
# Use the 'version_file_template' directive if possible to avoid type hints and annotations (python <3.8)
setuptools_scm_version = pkg_resources.get_distribution("setuptools_scm").version
# for some reason importing packaging.version.Version here fails on python 3.5
# from packaging.version import Version
# if Version(setuptools_scm_version) >= Version('6'):
setuptools_scm_version_major = int(setuptools_scm_version.split(".")[0])
if setuptools_scm_version_major >= 6:
    # template_arg_name = "version_file_template" if Version(setuptools_scm_version) >= Version('8.1') else "write_to_template"
    # print(Version(setuptools_scm_version))
    # print(template_arg_name)

    # Note that it was named 'write_to_template' earlier. But at that time it was not generating annotations so no need.
    args["write_to_template"] = """# file generated by setuptools_scm and customized
# don't change, don't track in version control
__version__ = version = '{version}'
__version_tuple__ = version_tuple = {version_tuple}
"""
# (3) Call setup() with as little args as possible
setup(
    download_url=DOWNLOAD_URL,
    use_scm_version=args
)
