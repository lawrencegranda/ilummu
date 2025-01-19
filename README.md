# ilummu - EdTech

This repository contains the API code that runs the application.

## A - Python Dependencies

- [pyenv](https://pypi.org/project/pyenv/): Pyenv is a python version manager that lets you easily switch between multiple versions of Python. We use it to configure the python environment.
- [poetry](https://python-poetry.org/docs/): Poetry is a virtual environment manager (similar to virtualenv)
- [python 3.10.7](): Must have this python version to run the app(install it using pyenv)

---

## B - Developper WorkStation Setup

Here are the tools that we are currently using:

- [MAMP](https://www.mamp.info/en/mamp/mac/) : MAMP is a local server environment that we use to run our MySQL database locally.
- [PostmanAPI](https://www.postman.com/downloads/) : Postman is an API platform for building and using APIs. It allows to make queries to endpoints and test performance.
- [SequelAce](https://apps.apple.com/us/app/sequel-ace/id1518036000?ls=1) : Database client used to connect to database running locally as well as databases hosted on AWS.

For everyone in the team to work with the same tools, please install these from the provided links.

---

## C - Running the code

To run the API, run the following steps:

1. Install the correct python version:
   - Run `pyenv install 3.10.7`

2. Set python version to be the default for the project:
   - Go to `~/path/to/edify/`
     - Run `cd ~/path/to/edify/`
   - Run `pyenv install 3.10.7`

3. Install Dependencies from Poetry:
   - Go to `~/path/to/edify/`
     - Run `cd ~/path/to/edify/`
   - Create a virtual environment
     - Run `poetry init` and keep accepting default value (press <ENTER>)
   - Install all dependencies into the environment
     - Run `poetry install`

4. Activate virtual environment:
   - Run `poetry shell`

5. Add environment variables
   - Run `source env.sh` (or whatever the environment filed is named)

6. Set up the local database:
   - Make sure you have an `edify_local` database created and empty.
   - Run `flask db upgrade` to get the latest models.
   - Run `python setup.py` to populate constants.
   - Optional: Run `python setup_fake.py` to populate the databse with fake data.

8. Run web:
   - Run `python app.py`

Steps 1-2-3-6 only need to be done the first time.

Steps 4-5-7 must be run every time.

---

## CICD - Github Branches

There are 2 main branches in the continuous development and integration pipeline:

- `main` : Main branch in the repository. Once a feature developed on a separate branch is ready, it can be merged to `main`
- `PROD` : Production branch in the repository. Once code is tested, functional, and working in `main`, it can be merged to `PROD`. Any changes are automatically deployed to the working web.

---

## The ilummu Database model

The database model is defined under `models.py` using SQLAlchemy package.

For more information about the relationship between tables and other flows in the app, check out the following link <INSERT>

### Setting Up Database Migrations

#### 1. Initialize Flask-Migrate

To set up Flask-Migrate for managing database migrations, follow these steps:

```bash
flask db init
```

This command initializes a migrations directory in your project.

#### 2. Create Migrations

After making changes to your models (e.g., adding new tables or modifying existing ones), generate a migration script:

```bash
flask db migrate -m "Brief description of your changes"
```

This command compares the current state of your models with the state of the database and generates a migration script.

#### 3. Apply Migrations

Apply the generated migration script to the database:

```bash
flask db upgrade
```

This command applies the migration script to the database, making the necessary changes to match your updated models.

#### Additional Commands

- **Downgrade**: Roll back the last applied migration.

  ```bash
  flask db downgrade
  ```

- **Show Current Revision**: Display the current revision of the database.

  ```bash
  flask db current
  ```

- **Show History**: Show the revision history.
  ```bash
  flask db history
  ```

#### Notes

- Ensure your `models.py` (or equivalent file) reflects the changes you want to make to your database schema before running `flask db migrate`.
- Always review the generated migration script (`versions/*.py`) to verify it accurately reflects the intended changes.
- Use caution with `flask db downgrade` as it can lead to data loss if not used carefully.

#### Example Workflow

1. Modify your SQLAlchemy models in `models.py`.
2. Run `flask db migrate -m "Added User table"`.
3. Review the generated migration script in `migrations/versions/`.
4. Apply the migration to your database with `flask db upgrade`.

---
