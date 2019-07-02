# -*- encoding: utf-8 -*-
# import uuid

# from XNBackend.app.extensions import cache

# SEPARATOR = ':'
# MAIN_PREFIX = 'TelecomMonitorTool'

# # set containing all registered devices IMEI
# IMEI_SET = SEPARATOR.join([MAIN_PREFIX, 'imei', 'all'])
# # devices IMEI to device info cache
# IMEI_DETAILS_PREFIX = SEPARATOR.join([MAIN_PREFIX, 'device', 'imei', ''])
# # devices ID to device info cache
# DEVICE_ID_DETAILS_PREFIX = SEPARATOR.join([MAIN_PREFIX, 'device', 'id', ''])


# @cache.memoize()
# def key_detail_by_imei(imei):
#     return IMEI_DETAILS_PREFIX + imei


# @cache.memoize()
# def key_detail_by_device_id(device_id):
#     return DEVICE_ID_DETAILS_PREFIX + uuid.UUID(hex=device_id).hex
