"""Shared graph connection, explicitly restricted to this lab's database."""
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from lumi_core.settings import neo4j as neo4j_settings


def database():
    return neo4j_settings().database

def get_driver():
    settings = neo4j_settings()
    driver = GraphDatabase.driver(settings.uri, auth=(settings.username, settings.password))
    try:
        driver.verify_connectivity()
    except Exception:
        driver.close()
        raise
    return driver


def run(driver, cypher, **params):
    records, _, _ = driver.execute_query(cypher, parameters_=params, database_=database())
    return [record.data() for record in records]
