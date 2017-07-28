# -*- coding: utf-8 -*-
"""
service tries to guess locale from user.
"""
import logging
import os


def load_config(environment="DEBUG"):
    config = {}

    config["LOG_LEVEL"] = logging.INFO
    config["DB"] = "/data/tracking-data.db"

    if not environment == "DEBUG":
        config["LOG_LEVEL"] = logging.INFO

    return config
