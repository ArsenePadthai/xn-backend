# -*- encoding: utf-8 -*-
# from XNBackend.api import api_client
# from XNBackend.api.iterator import DeviceIterator
# from XNBackend.app.extensions import redis
# from XNBackend.cache import key, util
# from XNBackend.cache.base import CacheBase


# class DeviceCache(CacheBase):
#     def build(self):
#         for device in DeviceIterator(api_client, page_size=100):
#             imei = device['deviceInfo']['nodeId']
#             device_id = device['deviceId']
#             detail = dict(device['deviceInfo'])
#             detail['deviceId'] = device_id
#             redis.sadd(key.IMEI_SET, imei)
#             redis.hmset(key.key_detail_by_imei(imei), detail)
#             redis.hmset(key.key_detail_by_device_id(device_id), detail)

#     def clean(self):
#         redis.delete(key.IMEI_SET)
#         util.remove_keys(key.IMEI_DETAILS_PREFIX)
#         util.remove_keys(key.DEVICE_ID_DETAILS_PREFIX)

#     @staticmethod
#     def search_id_by_imei(imei, partial=True):
#         if partial:
#             imei = '*' + imei + '*'
#         ans = set()
#         for imei in redis.sscan_iter(key.IMEI_SET, match=imei):
#             device_id = redis.hget(key.key_detail_by_imei(imei), 'deviceId')
#             if device_id:
#                 ans.add((imei, device_id))
#         return ans

#     @staticmethod
#     def search_device_by_id(id_):
#         return redis.hgetall(key.key_detail_by_device_id(id_))

#     @staticmethod
#     def iter_cached_devices():
#         for imei in redis.sscan_iter(key.IMEI_SET):
#             yield redis.hgetall(key.key_detail_by_imei(imei))
