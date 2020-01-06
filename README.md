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
> eco mode used to detect spare rooms. For spare rooms, light will be automatically turned off to save energy.

##### There are some design strategies for eco mode
1. There are two modes under ECO mode.
    * Work Mode: **between 8:00 and 17:00**
    * Offwork mode: **rest**

2. For each room, there is a flag to mark the room. If this room is marked as eco mode. Then backend task will periodically 
check the room - if it is an empty room. If the marked room meets some criterion during periodic check, then actions will be
triggered.


3. Actions
   * Turning off main light and set air condition to fan mode.
   * Turning both main light and aux light off, and setting air condition to fan mode.

4. How to set ECO mode?
    * From switch panel, there is an eco mode setting buttons, press the button for a specific room, the room will be marked
    as eco mode room.
    * eco mode setting api - just for demo!
   
5. Eco exit mechanism
    * when eco mode is active, pressing that eco button again will disable eco mode.
    * when a person press light button will disable eco mode for one eco cycle.

6. Conditions to trigger actions in eco mode \
   Use a prefix ```IRCOUNT_``` in redis to store how many times a room is identified as an empty room. For example, 
   A key IRCOUNT_501 stores a value how many times 501 is identified as empty. 
   
   * If a room is empty at the checkpoint, the IRCOUNT_ value will +1 without any question.
   * If a room is occupied at the checkpoint, and if the value is 1, then reset it to zero.
   * if the value of IRCOUNT_ is exactly 2, then execute eco action.
  
7. Condition to cancel eco mode  \
Eco cancellation condition actually conflicts with ZLAN tcp heartbeat mechanism. The heartbeat mechanism has to be removed
to get eco cancellation to work.


### blueprint make alarm service as microservice




 