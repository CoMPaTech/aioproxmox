#!/usr/bin/env sh
pytest tests --cov=aioproxmox --cov-report term-missing "${1}"
