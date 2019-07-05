## Development Environment Setup

### Prerequisites

* [Install Python >=3.6, <3.7](https://www.python.org/downloads/) (production VMs only preinstall 3.6)
* [Install Pipenv](https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv)



### Setup

```shell
git clone https://bitbucket.org/huangloong/xn-backend.git
cd xn-backend
pipenv install
cp XNBackend/settings.cfg.example XNBackend/settings.cfg
```



## Start Development Server

### Linux

```shell
export XN_SETTINGS=../settings.cfg
export FLASK_APP=XNBackend.app.entry
pipenv run flask run
```



### Windows CMD

```powershell
SET XN_SETTINGS=../settings.cfg
SET FLASK_APP=XNBackend.app.entry
pipenv run flask run
```

