import redis
import json
import random
from flask_restful import Resource, reqparse
from flask import current_app

R = redis.Redis(host='127.0.0.1', port=6379)

floor_parser = reqparse.RequestParser()
floor_parser.add_argument('floor',
                          required=True,
                          type=int,
                          help='require floor number')


class Energy(Resource):
    """
    MEASURE_LIGHT = 0
    MEASURE_AC = 1
    MEASURE_SOCKET = 2
    """

    @staticmethod
    def get_room_data(room_no):
        data = []
        for i in range(0, 3):
            key = '_'.join(['RTE', room_no, str(i)])
            value = (0, 0) if not R.get(key) else json.loads(R.get(key))
            data.append(value)
        return data

    def get_floor_data(self, floor):
        floor_light_power = 0
        floor_ac_power = 0
        floor_socket_power = 0

        floor_room_mapping = current_app.config['FLOOR_ROOM_MAPPING']
        for room in floor_room_mapping[floor]:
            room_data = self.get_room_data(str(room))
            floor_light_power += room_data[0][0]
            floor_ac_power += room_data[1][0]
            floor_socket_power += room_data[2][0]

        people_count = current_app.config['PEOPLE_COUNT'][floor]
        total_water = random.randint(300, 400)
        avg_water = int(total_water/people_count)
        avg_area = int(1000/people_count)
        kitchen = 0 if floor == 7 else random.randint(30, 60)
        total_power = floor_light_power + floor_ac_power + floor_socket_power
        money = int(total_power * current_app.config['UNIT_PRICE'])
        avg_elec = int(total_power/people_count)

        return {
            "total": total_power,
            "water": total_water,
            "money": money,
            "average_electric": avg_elec,
            "average_water": avg_water,
            "average_by_area": avg_area,
            "ac_main": floor_ac_power,
            "ac_inner": floor_ac_power,
            "socket": floor_socket_power,
            "light": floor_light_power,
            "kitchen": kitchen
        }

    def get(self):
        floors = [3, 4, 5, 6, 7, 9]
        ret = dict()
        building_power = 0
        building_water = 0
        ac_main = 0
        ac_inner = 0
        socket = 0
        light = 0
        kitchen = 0
        peopel_all = sum(current_app.config['PEOPLE_COUNT'])

        for f in floors:
            floor_data = self.get_floor_data(f)
            ret[str(f)+'f'] = floor_data
            building_power += floor_data['total']
            building_water += floor_data['water']
            ac_main += floor_data['ac_main']
            ac_inner += floor_data['ac_inner']
            socket += floor_data['socket']
            light += floor_data['light']
            kitchen += floor_data['kitchen']

        ret['total'] = {
            "total": building_power,
            "water": building_water,
            "money": int(building_power*current_app.config['UNIT_PRICE']),
            "average_electric": int(building_power/peopel_all),
            "average_water": int(building_water/peopel_all),
            "average_by_area": int(10000/peopel_all),
            "ac_main": ac_main,
            "ac_inner": ac_inner,
            "socket": socket,
            "light": light,
            "kitchen": kitchen
        }

        return ret


class EnergyShow(Resource):
    def get_r_value(self, key):
        value = R.get(key)
        return (0, 0) if not value else json.loads(value)

    def get(self):
        args = floor_parser.parse_args()
        floor = args.get('floor')

        floor_room_map = current_app.config['FLOOR_ROOM_MAPPING']
        data_dict = dict()
        for room in floor_room_map[floor]:
            light_key = '_'.join(['RTE', str(room), '0'])
            ac_key = '_'.join(['RTE', str(room), '1'])
            socket_key = '_'.join(['RTE', str(room), '2'])

            light_value = self.get_r_value(light_key)
            ac_value = self.get_r_value(ac_key)
            socket_value = self.get_r_value(socket_key)
            room_power = light_value[0] + ac_value[0] + socket_value[0]

            data_dict[str(room)] = (room_power, light_value[0], ac_value[0], socket_value[0])
        #return data_dict
        return sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
