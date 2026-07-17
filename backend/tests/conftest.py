# Tests always run against the dedicated test DB — never the dev DB.
# (Test runs used to fill the dev DB with junk faculties/teachers.)
import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://smartcampus:smartcampus@localhost:5432/smartcampus_test",
)
