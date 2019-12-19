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


## 设计相关

### 卓岚设备
### 卓岚设备对接控灯面板， 同时也对接红外传感器

update 2019.12.02 决定对于红外设备，不采用latest_record_id, 删除IRSensorStatus这张表, 以及删除IRSensors中的column (latest_record_id, latest_record)

### ECO Design Memo
#### Definition
1. There are two modes under ECO mode. One is work mode, the other is off-work mode. 
If current time is *between 8:00 and 17:00*, it is under work mode. If current time 
is out of previous time range, it is off work mode.

2. Under ECO mode, if certain conditions are satisfied (will be defined below), 
the server will take certain actions. 
```For work mode, actions will be turning off main light and set air condition to fan mode.```
```For off work mode, actions will be turning both main light and aux light off, and setting air condition to fan mode.```

3. How to set ECO mode?








 