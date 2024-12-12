from datetime import datetime
import pytz

test_meas_dict_list = [
    {
        'datetime': datetime.now(tz=pytz.utc).isoformat(),
        'meas_point': 'raspi1',
        'sensor_name': 'tank_links',
        'max_val': 155,
        'warn': 70,
        'alarm': 90,
        'values': [
            31.34562,
            31.34561,
            31.34562,
            31.34563,
            31.345625
        ]
    },
    {
        'datetime': datetime.now(tz=pytz.utc).isoformat(),
        'meas_point': 'raspi1',
        'sensor_name': 'tank_rechts',
        'max_val': 155,
        'warn': 70,
        'alarm': 90,
        'values': [
            29.34562,
            29.34561,
            29.34562,
            29.34563,
            29.345625
        ]
    },
{
        'datetime': datetime.now(tz=pytz.utc).isoformat(),
        'meas_point': 'raspi2',
        'sensor_name': 'tank1',
        'max_val': 155,
        'warn': 40,
        'alarm': 20,
        'values': [
            129.34562,
            129.34561,
            129.34562,
            129.34563,
            129.345625
        ]
    },
]
test_meas_dict_fail = {
    'datetime': datetime.now(tz=pytz.utc).isoformat(),
    'meas_point': 'measurement_pi_1',
    'sensor_id': 5,
    'values': [
        ';DROP DATABASE BLA BLA',
        1.34561,
        1.34562,
        1.34563,
        1.345625
    ]
}