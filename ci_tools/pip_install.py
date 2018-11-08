"""
equivalent of pip install -r <file>
 - with environment variables replacement
 - and all dependencies are installed in one 'pip install' call (solving potential complex deps)
"""
import os

import re
import sys
import pip


def install(packages):
    # for package in packages:
    #     pip.main(['install', package])
    all_pkgs_str = " ".join(all_pkgs)
    print("INSTALLING: pip install " + all_pkgs_str)
    pip.main(['install'] + packages)


env_var_regexp = re.compile(".*\$(\S+).*")


if __name__ == '__main__':
    assert len(sys.argv[1:]) == 1, "one mandatory filename argument should be provided"

    filename = sys.argv[1]

    with open(filename) as f:
        all_pkgs = []
        for line in f.readlines():
            # First remove any comment on that line
            splitted = line.split('#', maxsplit=1)
            splitted = splitted[0].strip().rstrip()
            if splitted != '':
                # the replace env vars
                env_var_found=True
                while env_var_found:
                    res = env_var_regexp.match(splitted)
                    env_var_found = res is not None
                    if env_var_found:
                        env_var_name = res.groups()[0]
                        try:
                            env_var_val = os.environ[env_var_name]
                            print("replacing $%s with %s" % (env_var_name, env_var_val))
                            splitted = splitted.replace("$%s" % env_var_name, env_var_val)
                        except KeyError:
                            raise Exception("Environment variable does not exist in file %s: $%s"
                                            "" % (filename, env_var_name))
                    else:
                        all_pkgs.append(splitted)

        install(all_pkgs)
