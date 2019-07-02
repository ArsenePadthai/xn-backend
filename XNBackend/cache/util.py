# -*- encoding: utf-8 -*-
# from XNBackend.app.extensions import redis

# _remove_keys_script = None


# def remove_keys(key_prefix:str):
#     global _remove_keys_script
#     if not _remove_keys_script:
#         _remove_keys_script = redis.register_script(
#             '''local keys = redis.call('keys', ARGV[1])
#             for i=1,#keys,5000 do
#                 redis.call('del', unpack(keys, i, math.min(i+4999, #keys)))
#             end
#             return keys'''
#         )
#     _remove_keys_script(args=[key_prefix + '*',])
