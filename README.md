# SearchAndDoc

Discord app that enhances the search feature and utilizes LLMs to create documentation of anything related to the project info discussed in channels.

## Requirements
- Python >= 3.9
- pyenv

## Setup

```shell
# To delete virtual env:
pyenv virtualenv-delete <venv-name>
# or
pyenv uninstall 3.9.21/envs/pyenv-3.9.21 (python-version/envs/name_of_virtual_env)

# To install python3.9.20:
CONFIGURE_OPTS="--with-openssl=/opt/Homebrew/Cellar/openssl@3/3.4.1" pyenv install -v 3.9.20

# To set up the python version:
pyenv local 3.9.20

# To create virtual env:
pyenv virtualenv 3.9.20 virtual_env_name

# To check current virtual environments:
pyenv versions

# To activate virtual env:
pyenv activate virtual_env_name

# To find where python3.9 was installed:
pyenv which python

## Run Pre-Commit
```shell
pre-commit run -a
```

## Run tests
```shell
python3 -m pytest
```

## Run Server
```shell
uvicorn main:app --reload
```
