from flask_restful import Resource
from XNBackend.models import S3FC20
from functools import partial

FLOOR3 = 0
FLOOR4 = 1
FLOOR5 = 2
FLOOR6 = 3
FLOOR7 = 4


def check_divisor_zero(dividend, divisor):
    return 0 if divisor == 0 else float('%.2f' % (dividend / divisor))


def form_floor_data(floor_str, floor_index, elec=None, water=None, money=None,
                    people=None, area=None, ac=None, socket=None, light=None, kitchen=None):
    avg_elec = check_divisor_zero(elec[floor_index], people[floor_index])
    avg_water = check_divisor_zero(elec[floor_index], people[floor_index])
    avg_by_area = check_divisor_zero(elec[floor_index], area[floor_index])

    return {
        floor_str: {
            "total": elec[floor_index],
            "water": water[floor_index],
            "money": money[floor_index],
            "average_electric": avg_elec,
            "average_water": avg_water,
            "average_by_area": avg_by_area,
            "ac_main": ac[floor_index],
            "ac_inner": ac[floor_index],
            "socket": socket[floor_index],
            "light": light[floor_index],
            "kitchen": kitchen[floor_index],
        }
    }


class Energy(Resource):

    def get(self):
        MEASURE_LIGHT = 0
        # TODO add ac later
        # MEASURE_AC = 1
        MEASURE_SOCKET = 2
        # TODO check area
        area_all = [300, 310, 305, 297, 312]
        kitchen_all = [460, 341, 421, 164, 235]
        people_all = [137, 87, 107, 90, 123]

        elec_all = [0, 0, 0, 0, 0]  # 3f, 4f, 5f, 6f, 7f
        ac_all = [2, 3, 2, 3, 4]
        light_all = [0, 0, 0, 0, 0]
        socket_all = [0, 0, 0, 0, 0]

        elec_3f = S3FC20.query.filter(S3FC20.locator.has(floor=3))
        elec_3f_light = elec_3f.filter(S3FC20.measure_type == MEASURE_LIGHT)
        # elec_3f_ac = elec_3f.filter(S3FC20.measure_type == MEASURE_AC)
        elec_3f_socket = elec_3f.filter(S3FC20.measure_type == MEASURE_SOCKET)

        # sum
        for i in elec_3f_light.all():
            if i.latest_record:
                light_all[FLOOR3] += i.latest_record.gW
        ac_all[FLOOR3] = 200
        for i in elec_3f_socket.all():
            if i.latest_record:
                socket_all[FLOOR3] += i.latest_record.gW
        for i in elec_3f.all():
            if i.latest_record:
                elec_all[FLOOR3] += i.latest_record.gW

        elec_all[FLOOR4] = 600
        elec_all[FLOOR5] = 600
        elec_all[FLOOR6] = 600
        elec_all[FLOOR7] = 600

        water_all = [400, 500, 300, 230, 280]

        # TODO need to adjust the factor 1.4
        money_all = [1.4*i for i in elec_all]

        total_avg_elec = check_divisor_zero(sum(elec_all), sum(people_all))
        total_avg_water = check_divisor_zero(sum(water_all), sum(people_all))
        total_avg_by_area = check_divisor_zero(sum(elec_all), sum(area_all))

        return_data = {
            "total": {
                "total": sum(elec_all),
                "water": sum(water_all),
                "money": sum(money_all),
                "average_electric": total_avg_elec,
                "average_water": total_avg_water,
                "average_by_area": total_avg_by_area,
                "ac_main": sum(ac_all),
                "ac_inner": sum(ac_all),
                "socket": sum(socket_all),
                "light": sum(light_all),
                "kitchen": sum(kitchen_all),
            }
        }

        get_floor_data = partial(form_floor_data, elec=elec_all, water=water_all, money=money_all, people=people_all,
                                 area=area_all, ac=ac_all, socket=socket_all, light=light_all, kitchen=kitchen_all)

        return_data.update(get_floor_data('3f', FLOOR3))
        return_data.update(get_floor_data('4f', FLOOR4))
        return_data.update(get_floor_data('5f', FLOOR5))
        return_data.update(get_floor_data('6f', FLOOR6))
        return_data.update(get_floor_data('7f', FLOOR7))

        return return_data
