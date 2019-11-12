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





## Create Database

### trouble

```
(1832, "Cannot change column 'user_id': used in a foreign key constraint 'user_logins_ibfk_1'")
```

### solution

* 执行```show create table user_logins ```查询外键约束名
* 解除外键约束:```alter table user_logins drop foreign key + 查询到的外键约束名```
* 重新执行```alembic upgrade head```



# 设计相关






 