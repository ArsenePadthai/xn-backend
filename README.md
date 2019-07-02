## Development Environment Setup

### Prerequisites

* [Install Python >=3.6, <3.7](https://www.python.org/downloads/) (production VMs only preinstall 3.6)
* [Install Pipenv](https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv)



### Setup

```shell
git clone https://bitbucket.org/huangloong/wf-dashboard.git
cd wf-dashboard
pipenv install
cp WFDashboard/settings.cfg.example WFDashboard/settings.cfg
```



## Start Development Server

### Linux

```shell
export WF_SETTINGS=../settings.cfg
export FLASK_APP=WFDashboard.app.entry
pipenv run flask run
```



### Windows CMD

```powershell
SET WF_SETTINGS=../settings.cfg
SET FLASK_APP=WFDashboard.app.entry
pipenv run flask run
```

