#!/usr/bin/env sh
pytest tests --cov=phais --cov-report term-missing "${1}"
