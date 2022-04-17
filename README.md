

## Setup and usage
Dependencies are managed with pipenv. To install them, run `pipenv install`. To run things within this environment, use `pipenv run` followed by the command to run, or `pipenv shell` to enter a shell inside this environment

The first time you use the script, you may also want to initialize a fresh database, which can be done by running the script and using the `--createdb` flag

## Unit tests
unit tests can be run with `pipenv run python3 -m unittest`


## Database versioning
This project uses [alembic](https://alembic.sqlalchemy.org/en/latest/) to keep track of schema changes to the database and allow for easy migration.

### Applying DB Upgrades
running `pipenv run alembic upgrade head` will upgrade your database to the latest version

### Creating DB Upgrades
The command for generating a database revision (i.e. if you change the schema) is `pipenv run alembic revision --autogenerate -m "<message>"`. a file will be generated in the `migrations/versions` folder that will need review and some cleanup as there are [some things it cannot detect](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect)