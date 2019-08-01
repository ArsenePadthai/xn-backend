## note
need to hack flask_restless 
https://github.com/jfinkels/flask-restless/issues/303
refer to pakdev's hack

## Control Worker

### Start Worker

* Modify WorkingDirectory and path of pipenv in systemd files

```python -m XNBackend.task.sensor.start```

### Stop Worker

```python -m XNBackend.task.sensor.stop```
