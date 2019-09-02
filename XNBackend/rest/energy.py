from flask_restful import Resource
from XNBackend.models import S3FC20


FLOOR3 = 0
FLOOR4 = 1
FLOOR5 = 2
FLOOR6 = 3
FLOOR7 = 4


class Energy(Resource):

    def get(self):
        MEASURE_LIGHT = 0
        MEASURE_AC = 1
        MEASURE_SOCKET = 2
        area_size = [300, 310, 305, 297, 312]
        stored_energy_total = [460, 341, 421, 164, 235]
        people_count = [1, 1, 1, 1, 1]  # zero people logic

        elec_total = [0, 0, 0, 0, 0]  # 3f, 4f, 5f, 6f, 7f
        elec_ac_total = [2, 3, 2, 3, 4]
        elec_light_total = [0, 0, 0, 0, 0]
        elec_socket_total = [0, 0, 0, 0, 0]

        elec_3f = S3FC20.query.filter(S3FC20.locator.has(floor=3))
        elec_3f_light = elec_3f.filter(S3FC20.measure_type == MEASURE_LIGHT)
        # elec_3f_ac = elec_3f.filter(S3FC20.measure_type == MEASURE_AC)
        elec_3f_socket = elec_3f.filter(S3FC20.measure_type == MEASURE_SOCKET)

        # sum
        for i in elec_3f_light.all():
            elec_light_total[FLOOR3] += i.latest_record.gW
        elec_ac_total[FLOOR3] = 200
        for i in elec_3f_socket.all():
            elec_socket_total[FLOOR3] += i.latest_record.gW
        for i in elec_3f.all():
            elec_total[FLOOR3] += i.latest_record.gW

        elec_total[FLOOR4] = 600
        elec_total[FLOOR5] = 600
        elec_total[FLOOR6] = 600
        elec_total[FLOOR7] = 600

        water_total = [400, 500, 300, 230, 280]

        expense = [350, 640, 562, 354, 645]

        return {
            "total": {
                "total": sum(elec_total),
                "water": sum(water_total),
                "money": sum(expense),
                "average_electric": sum(elec_total) / sum(people_count),
                "average_water": sum(water_total) / sum(people_count),
                "average_by_area": sum(elec_total) / sum(area_size),
                "ac_main": sum(elec_ac_total),
                "ac_inner": sum(elec_ac_total),
                "socket": sum(elec_socket_total),
                "light": sum(elec_light_total),
                "stored_energy": sum(stored_energy_total),
            },
            "3f": {
                "total": elec_total[FLOOR3],
                "water": water_total[FLOOR3],
                "money": expense[FLOOR3],
                "average_electric": elec_total[FLOOR3] / people_count[FLOOR3],
                "average_water": water_total[FLOOR3] / people_count[FLOOR3],
                "average_by_area": elec_total[FLOOR3] / area_size[FLOOR3],
                "ac_main": elec_ac_total[FLOOR3],
                "ac_inner": elec_ac_total[FLOOR3],
                "socket": elec_socket_total[FLOOR3],
                "light": elec_light_total[FLOOR3],
                "stored_energy": stored_energy_total[FLOOR3],
            },
            "4f": {
                "total": elec_total[FLOOR4],
                "water": water_total[FLOOR4],
                "money": expense[FLOOR4],
                "average_electric": elec_total[FLOOR4] / people_count[FLOOR4],
                "average_water": water_total[FLOOR4] / people_count[FLOOR4],
                "average_by_area": elec_total[FLOOR4] / area_size[FLOOR4],
                "ac_main": elec_ac_total[FLOOR4],
                "ac_inner": elec_ac_total[FLOOR4],
                "socket": elec_socket_total[FLOOR4],
                "light": elec_light_total[FLOOR4],
                "stored_energy": stored_energy_total[FLOOR4],
            },
            "5f": {
                "total": elec_total[FLOOR5],
                "water": water_total[FLOOR5],
                "money": expense[FLOOR5],
                "average_electric": elec_total[FLOOR5] / people_count[FLOOR5],
                "average_water": water_total[FLOOR5] / people_count[FLOOR5],
                "average_by_area": elec_total[FLOOR5] / area_size[FLOOR5],
                "ac_main": elec_ac_total[FLOOR5],
                "ac_inner": elec_ac_total[FLOOR5],
                "socket": elec_socket_total[FLOOR5],
                "light": elec_light_total[FLOOR5],
                "stored_energy": stored_energy_total[FLOOR5],
            },
            "6f": {
                "total": elec_total[FLOOR6],
                "water": water_total[FLOOR6],
                "money": expense[FLOOR6],
                "average_electric": elec_total[FLOOR6] / people_count[FLOOR6],
                "average_water": water_total[FLOOR6] / people_count[FLOOR6],
                "average_by_area": elec_total[FLOOR6] / area_size[FLOOR6],
                "ac_main": elec_ac_total[FLOOR6],
                "ac_inner": elec_ac_total[FLOOR6],
                "socket": elec_socket_total[FLOOR6],
                "light": elec_light_total[FLOOR6],
                "stored_energy": stored_energy_total[FLOOR6],
            },
            "7f": {
                "total": elec_total[FLOOR7],
                "water": water_total[FLOOR7],
                "money": expense[FLOOR7],
                "average_electric": elec_total[FLOOR7] / people_count[FLOOR7],
                "average_water": water_total[FLOOR7] / people_count[FLOOR7],
                "average_by_area": elec_total[FLOOR7] / area_size[FLOOR7],
                "ac_main": elec_ac_total[FLOOR7],
                "ac_inner": elec_ac_total[FLOOR7],
                "socket": elec_socket_total[FLOOR7],
                "light": elec_light_total[FLOOR7],
                "stored_energy": stored_energy_total[FLOOR7],
            }
        }
