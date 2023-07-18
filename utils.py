from datetime import datetime
import argparse
import json
import sys
import os


NEP_ENG_NUMS: dict[str:str] = {
    '०': '0',
    '१': '1',
    '२': '2',
    '३': '3',
    '४': '4',
    '५': '5',
    '६': '6',
    '७': '7',
    '८': '8',
    '९': '9'
    }
MONTHS: list[str] = [
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december'
    ]
NEP_MONTHS: list[str] = [
    'बैशाख', 'जेष्ठ', 'आषाढ़', 'श्रावण', 'भाद्र', 'आश्विन',
    'कार्तिक', 'मंसिर', 'पौष', 'माघ', 'फाल्गुन', 'चैत्र'
    ]

Y: int = datetime.today().year
M: int = datetime.today().month
D: int = datetime.today().day

KHOLIDAY_HEADER: str = f'''
::
:: Country:  Nepal
::
:: Language: Nepali
::
:: Author:   CausalSnek <contact@casualsnek.eu.org>
::
:: Updated:  {Y}-{M}-{D}
::
:: Source:   https://api.casualsnek.eu.org/nepcalev/2080
::           https://github.com/casualsnek/nepcalev
:: Metadata
country     "NP"
language    "np"
name        "National events for Nepal"
description "National events file for Nepal includes %EVENT_TYPES%"
'''.strip()


def nep_date_to_str(date: str) -> str:
    """
    Converts nepali date to string
    :param date: Date
    :return:
    """
    date_parts: list = date.split('/')
    nep_numeric_day: str = ''.join(
        list(NEP_ENG_NUMS.keys())[int(num_char)] for num_char in date_parts[2]
        )
    nep_month_name: str = NEP_MONTHS[int(date_parts[1])-1]
    nep_numeric_year: str = ''.join(
        list(NEP_ENG_NUMS.keys())[int(num_char)] for num_char in date_parts[0]
        )
    return f'{nep_month_name} {nep_numeric_day}, {nep_numeric_year}'


def get_kholiday_line(date: str, event_data: dict, event_types: list[str],
                      out_dict: dict, append_bida: bool,
                      append_panchangam: bool, flatten_holidays: bool) -> None:
    """
    Generates a line for kholiday entry
    :param date: Date
    :param event_data: Events data from artifact
    :param event_types: Event types to keep
    :param out_dict: The dictionary where the lines will be appended
    :param append_bida: Add bida in front of holidays
    :param append_panchangam: Add panchangam information
    :param flatten_holidays: Merge all holidays in a day to one
    :return:
    """
    month: str = MONTHS[int(date.split('/')[1])-1]
    day: str = date.split('/')[2]
    year: str = date.split('/')[0]
    if 'holidays' in event_types:
        if event_data['is_public_holiday']:
            if flatten_holidays:
                flat_events: str = '/'.join(
                    event for event in event_data['events']
                    )
                out_dict[':: Public Holidays'].append(
                    f'"{"सार्बजनिक बिदा: " if append_bida else ""}'
                    f'{flat_events}" public on { month } { day } { year }'
                    )
            else:
                for event in event_data['events']:
                    out_dict[':: Public Holidays'].append(
                        f'"{"सार्बजनिक बिदा: " if append_bida else ""}'
                        f'{ event }" public on { month } { day } { year }'
                        )

    if 'non_holiday_events' in event_types:
        if not event_data['is_public_holiday']:
            for event in event_data['events']:
                out_dict[':: Civil'].append(
                    f'"{ event }" civil on { month } { day } { year }'
                    )

    if 'nepali_date' in event_types:
        out_dict[':: Bikram Sambat Dates'].append(
            f'"{ nep_date_to_str(event_data["nepali_date"]) }" '
            f'nameday on { month } { day } { year }'
            )

    if 'tithi' in event_types:
        out_dict[':: Nepali Tithis'].append(
            f'"{ event_data["tithi"]} " nameday on { month } { day } { year }'
            )

    if 'panchangam' in event_types:
        for event in event_data['panchangam']:
            out_dict[':: Panchangam'].append(
                f'"{"पञ्चाङ्ग:" if append_panchangam else ""}'
                f'{ event }" nameday on { month } { day } { year }'
                )

    return None


if __name__ == '__main__':
    about = """
            casualsnek/npEventsAPI

    Author       : Casual Snek (@casualsnek on GitHub)
    License      : GNU GENERAL PUBLIC LICENSE v2
    Email        : casualsnek@protonmail.com
    """
    parser = argparse.ArgumentParser(
        description=about,
        formatter_class=argparse.RawDescriptionHelpFormatter
        )
    parser.add_argument(
        '-k', '--geneout_dictrate-kholiday',
        help='Generate kholiday holiday entry file from json artifact',
        action='store_true', dest='k'
        )
    parser.add_argument(
        '-ah', '--append-holiday-info',
        help='Append "Sarbajanik Bida" in front of holiday events, '
        'Use with "-k" flag ',
        action='store_true', dest='ah')
    parser.add_argument(
        '-ap', '--append-panchangam-info',
        help='Append "Panchangam" in front of panchangam events, '
        'Use with "-k" flag ',
        action='store_true', dest='ap')
    parser.add_argument(
        '-fh', '--flatten-holidays',
        help='Flatten holiday events into one.  Use with "-k" flag',
        action='store_true', dest='fh'
        )
    parser.add_argument(
        '-ia', '--input-artifact', dest='input_artifacts',
        help='Artifact to use for generating kholiday data. '
        'Use with "-k" flag. '
        'Can be used multiple time to use multiple artifacts',
        required=False, action='append'
        )
    parser.add_argument(
        '-se', '--select-events', dest='events',
        help='Event types to include while generating kholiday data. '
        'Comma seperated. '
        'Use with "-k" flag. '
        'Available options: holidays,nepali_date,'
        'panchangam,tithi,non_holiday_events',
        default='holidays,nepali_date,panchangam,tithi,non_holiday_events',
        required=False
        )
    parser.add_argument(
        '-hod', '--holiday-out-dir', dest='out_dir_holiday',
        help='kholiday output file path. Use with "-k" flag',
        default=os.path.dirname(os.path.abspath(__file__)),
        required=False
        )

    args = parser.parse_args()

    if args.k:
        print('[I] Kholiday file generation mode')
        events = {}

        for artifact in args.input_artifacts:
            if not os.path.isfile(os.path.abspath(artifact)):
                print(
                    f'[E] One of the input artifact at '
                    f'"{os.path.abspath(artifact)}" does not exist. '
                    f'Terminating..'
                    )
                sys.exit(1)
        for artifact in args.input_artifacts:
            with open(os.path.abspath(artifact), 'r') as af:
                events = {**events, **json.load(af)}
        holiday_types: dict = {
            ':: Public Holidays': [],
            ':: Civil': [],
            ':: Bikram Sambat Dates': [],
            ':: Nepali Tithis': [],
            ':: Panchangam': []
        }
        for eng_date in events:
            get_kholiday_line(
                eng_date, events[eng_date],
                event_types=args.events.split(','),
                out_dict=holiday_types,
                append_bida=args.ah,
                append_panchangam=args.ap,
                flatten_holidays=args.fh
                )
        print('[I] Creating output directory !')
        os.makedirs(os.path.abspath(args.out_dir_holiday), exist_ok=True)
        FILE_PATH: str = os.path.join(
            os.path.abspath(args.out_dir_holiday),
            f'holiday_np_np@{"_".join(ev for ev in args.events.split(",") )}'
            )
        with open(FILE_PATH, 'w') as hf:
            hf.write(KHOLIDAY_HEADER.replace(r'%EVENT_TYPES%', args.events))
            for h_type in holiday_types:
                hf.write(f'\n\n{h_type}')
                for holiday in holiday_types[h_type]:
                    hf.write(f'\n{holiday}')
        print(f'[S] Kholiday file generated at "{FILE_PATH}" !')
    if not args.a and not args.k:
        parser.print_help(sys.stderr)
