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

COVERAGE_FILE=".coverage.meta"
pytest --junitxml=reports/junit/junit.xml --html=reports/junit/report.html --cov-report term-missing --cov=./pytest_harvest -v pytest_harvest/tests/

COVERAGE_FILE=".coverage.raw"
pytest --cov-report term-missing --cov=./pytest_harvest -v pytest_harvest/tests_raw/

coverage combine
