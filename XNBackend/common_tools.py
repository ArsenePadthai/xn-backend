from datetime import datetime
import pytz


def conv_tz(dt, dist_tz, src_tz='utc'):
    assert isinstance(dt, datetime)
    aware_dt = dt.replace(tzinfo=src_tz)
    return aware_dt.astimezone(dist_tz)


if __name__ == '__main__':
    a = datetime.now()
    m = conv_tz(a,
                pytz.timezone('UTC'),
                src_tz=pytz.timezone('Asia/Shanghai'))
