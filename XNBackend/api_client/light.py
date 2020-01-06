from XNBackend.utils import query_panel_status


def sp_control_light(tcp_conn, sp, main=None, aux=None):
    """
    Args:
        tcp_conn: pre-built tcp connection to ZLAN port, for example: 10.100.102.8:4196
        sp: switch panel object returned by sqlalchemy query
        main: int, 1 means turn on, 0 means turn off
        aux: int, 1 means turn on, 0 means turn off
    """
    try:
        assert (main is not None) or (aux is not None)
        ret = query_panel_status(tcp_conn, sp.batch_no, sp.addr_no)
        print(ret.hex())
        s_1 = ret[-5]
        s_2 = ret[-4]
        s_3 = ret[-3]
        s_4 = ret[-2]
    except Exception as e:
        print(e)
        return -1, 'Failed to get panel status.'

    if sp.panel_type == 0:
        # is 4 buttons type
        if main is not None:
            s_1 = main
        if aux is not None:
            s_4 = aux

    elif sp.panel_type == 1:
        # is 2 buttons type
        if main is not None:
            s_1 = main
        if aux is not None:
            s_2 = aux
    four_bits = [s_1, s_2, s_3, s_4]

    addr_hex = hex(sp.addr_no)[2:].rjust(2, '0')
    cmd = bytes.fromhex(f'DA 06 {addr_hex} 02') + bytes(four_bits) + bytes.fromhex('EE')
    print(cmd.hex())
    try:
        tcp_conn.send(cmd)
        return 0, 'cmd sent successfully'
    except Exception as e:
        return -1, 'failed to send cmd to control light'
