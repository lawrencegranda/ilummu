# YouShift API - Night Shift Allocation for Hospitals
This repository contains the API code that runs the application.


## A - Python Dependencies
-----
- [pyenv](https://pypi.org/project/pyenv/): Pyenv is a python version manager that lets you easily switch between multiple versions of Python. We use it to configure the python environment.
- [poetry](https://python-poetry.org/docs/): Poetry is a virtual environment manager (similar to virtualenv)
- [python 3.10.7](): Must have this python version to run the app(install it using pyenv)


## B - Developper WorkStation Setup
----

Here are the tools that we are currently using:
- [MAMP](https://www.mamp.info/en/mamp/mac/) : MAMP is a local server environment that we use to run our MySQL database locally.
- [PostmanAPI](https://www.postman.com/downloads/) : Postman is an API platform for building and using APIs. It allows to make queries to endpoints and test performance.
- [SequelAce](https://apps.apple.com/us/app/sequel-ace/id1518036000?ls=1) : Database client used to connect to database running locally as well as databases hosted on AWS.

For everyone in the team to work with the same tools, please install these from the provided links.

## C - Running the code
----

To run the API, run the following steps:
1) Install the correct python version:
    * Run `pyenv install 3.10.7`
2) Set python version to be the default for the project:
    * Go to `~/path/to/edify/`
        + Run `cd ~/path/to/edify/`
    * Run `pyenv install 3.10.7`
3) Install Dependencies from Poetry:
    * Go to `~/path/to/edify/`
        + Run `cd ~/path/to/edify/`
    * Create a virtual environment
        + Run `poetry init` and keep accepting default value (press <ENTER>)
    * Install all dependencies into the environment
        + Run `poetry install`
  
4) Activate virtual environment:
    * Run `poetry shell`
5) Add environment variables
    * Run `source env.sh` (or whatever the environment filed is named)
6) Run API:
    * Run `python run.py`


Steps 1-2-3 only need to be done the first time. 

Steps 4-5-6 must be run every time,



## D - the Youshift Database model 
----
The database model is defined under `models.py` using SQLAlchemy package.

For more information about the relationship between tables and other flows in the app, check out the following link <INSERT>

## CICD - Github Branches
----
There is 1 main branch in the continuous development and integration pipeline:
* `main` : Main branch in the repository. Once a feature developed on a separate branch is ready, it can be merged to `main`