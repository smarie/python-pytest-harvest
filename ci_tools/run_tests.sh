#!/usr/bin/env bash

cleanup() {
    rv=$?
    # on exit code 1 this is normal (some tests failed), do not stop the build
    if [ "$rv" = "1" ]; then
        exit 0
    else
        exit $rv
    fi
}

trap "cleanup" INT TERM EXIT

#if hash pytest 2>/dev/null; then
#    echo "pytest found"
#else
#    echo "pytest not found. Trying py.test"
#fi

# First the raw for coverage
echo -e "\n\n****** Running tests : 1/2 RAW******\n\n"
coverage run --source pytest_harvest -m pytest -v pytest_harvest/tests_raw/
#python -m pytest --cov-report term-missing --cov=./pytest_harvest -v pytest_harvest/tests_raw/

# Then the meta (appended)
echo -e "\n\n****** Running tests : 2/2 META******\n\n"
python -m pytest --junitxml=reports/junit/junit.xml --html=reports/junit/report.html --cov-report term-missing --cov=./pytest_harvest --cov-append -v pytest_harvest/tests/
