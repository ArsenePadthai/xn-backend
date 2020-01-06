from flask_restful import fields


class MyDateTime(fields.Raw):
    def format(self, value):
        return value.strftime("%Y-%m-%d %H:%M:%S")


def extract_data(ac_data):
    data_dict = dict()
    data_dict['device_index_code'] = ac_data['deviceCode']
    data_dict['if_online'] = ac_data['online']
    for d in ac_data['variantDatas']:
        if d['code'] == 'FanSpeedSet':
            data_dict['set_speed'] = int(d['value'])
            continue
        if d['code'] == 'ModeCmd':
            data_dict['set_mode'] = int(d['value'])
            continue
        if d['code'] == 'RoomTemp':
            data_dict['temperature'] = int(d['value'])
            continue
        if d['code'] == 'StartStopStatus':
            data_dict['ac_on'] = True if int(d['value']) else False
            continue
        if d['code'] == 'TempSet':
            data_dict['set_temperature'] = int(d['value'])
    return data_dict


def ac_info_from_model(ac_model_instance):
    return {
        "device_index_code": ac_model_instance.device_index_code,
        "if_online": True if ac_model_instance.if_online else False,
        "set_speed": ac_model_instance.desired_speed,
        "set_mode": ac_model_instance.desired_mode,
        "temperature": ac_model_instance.temperature,
        "ac_on": True if ac_model_instance.ac_on else False,
        "set_temperature": ac_model_instance.desired_temperature
    }
