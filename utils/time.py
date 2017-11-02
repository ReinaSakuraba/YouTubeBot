import datetime

from dateutil.relativedelta import relativedelta


def human_time(seconds):
    seconds = int(seconds)
    if seconds == 0:
        return '0 seconds'

    is_negative = seconds < 0

    now = datetime.datetime.utcnow()
    future = now + datetime.timedelta(seconds=abs(seconds))
    delta = relativedelta(future, now)

    weeks, days = divmod(delta.days, 7)

    units = (
        ('year', delta.years),
        ('month', delta.months),
        ('week', weeks),
        ('day', days),
        ('hour', delta.hours),
        ('minute', delta.minutes),
        ('second', delta.seconds)
    )

    time = [f'{value} {unit}{"s" * (value != 1)}' for unit, value in units if value]

    if len(time) > 2:
        time = f'{", ".join(time[:-1])}, and {time[-1]}'
    else:
        time = ' and '.join(time)

    if is_negative:
        time += ' ago'
    return time
