from flask import Flask, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import json
import os
from sqlalchemy import or_, and_
from datetime import datetime


db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///calendar.db"
db.init_app(app)


class Calendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad_sn = db.Column(db.Integer, unique=True, nullable=False)
    bs_sn = db.Column(db.Integer, unique=True, nullable=False)
    ad_year = db.Column(db.Integer, unique=False, nullable=False)
    ad_month = db.Column(db.Integer, unique=False, nullable=False)
    ad_day = db.Column(db.Integer, unique=False, nullable=False)
    bs_year = db.Column(db.Integer, unique=False, nullable=False)
    bs_month = db.Column(db.Integer, unique=False, nullable=False)
    bs_day = db.Column(db.Integer, unique=False, nullable=False)
    is_holiday = db.Column(db.Boolean, unique=False, nullable=False,
                           default=False)


class Events(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.Unicode, unique=False, nullable=False)
    event_class = db.Column(db.String, unique=False, nullable=False)


class CalendarEventRelationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_id = db.Column(db.Integer, db.ForeignKey('calendar.id'),
                       nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'),
                         nullable=False)
    events = db.relationship('Events', backref='CalendarEventRelationship',
                             lazy=True)
    dates = db.relationship('Calendar', backref='CalendarEventRelationship',
                            lazy=True)


class CalendarQueryException(Exception):
    pass


def get_days_on(caltype: str, year: int, month: int):
    dbc = db.select(Calendar).filter(
            getattr(Calendar, f'{caltype}_year') == year,
            getattr(Calendar, f'{caltype}_month') == month
            ).order_by(
                getattr(Calendar, f'{caltype}_day').desc()
            )
    result = db.session.execute(dbc).first()
    return getattr(result[0], f'{caltype}_day')


def get_today(caltype: str):
    y = datetime.now().year
    m = datetime.now().month
    d = datetime.now().day
    if caltype == 'ad':
        return f'{y}-{m}-{d}'
    elif caltype == 'bs':
        dbc = db.select(Calendar).filter(
            Calendar.ad_year == y,
            Calendar.ad_month == m,
            Calendar.ad_day == d
            )
        r = db.session.execute(dbc).first()
        return f'{r[0].bs_year}-{r[0].bs_month}-{r[0].bs_day}'


def calendar_var_replace(caltype: str, string: str) -> str:
    string = string.replace(
        '@today', get_today(caltype=caltype)
        )
    string = string.replace(
        '@ignore', '0'
        )
    string = string.replace(
        '@cur_year', get_today(caltype=caltype).split('-')[0]
        )
    string = string.replace(
        '@cur_month', get_today(caltype=caltype).split('-')[1]
        )
    string = string.replace(
        '@cur_day', get_today(caltype=caltype).split('-')[2]
        )
    return string


def calender_query_builder(caltype: str, start: tuple[int, int, int],
                           only_holidays: bool = False,
                           except_holidays: bool = False,
                           filter_tithis: list[str] = [],
                           end: tuple[int, int, int] = (0, 1, 1),
                           search_event: str = ''):
    filter_tithis = [
        item for item in filter_tithis if item.strip() != ''
        ]
    calendar = db.select(Calendar)\
        .join(
            CalendarEventRelationship,
            Calendar.id == CalendarEventRelationship.day_id
            )\
        .group_by(Calendar.id) \
        .join(Events, CalendarEventRelationship.event_id == Events.id)
    if caltype not in ['ad', 'bs']:
        raise CalendarQueryException(f'Unspported calendar type \'{caltype}\'')
    if end[0] > start[0] and end[0] == 0:
        raise CalendarQueryException(
            'End date is ahead of start date, cannot compute'
            )
    if end[0] != 0:
        start_y, start_m, start_d = start[0], start[1], start[2]
        end_y, end_m, end_d = end[0], end[1], end[2]
        # Validate month
        if (start_m >= 0 and start_m <= 12) or (end_m >= 0 and end_m <= 12):
            start_m = start_m if start_m != 0 else 1
            end_m = end_m if end_m != 0 else 12  # Select last month for end
        else:
            raise CalendarQueryException(
                f' "{start_m}" or "{end_m}" is not a valid month parameter. '
                f'For range start use "0" to select first month of the year '
                f'and for range end use "0" to select last month of the year !'
                )
        start_d_data = get_days_on(caltype, start_y, start_m)
        end_d_data = get_days_on(caltype, end_y, end_m)
        # Validate day
        if (0 <= start_d <= start_d_data) \
                or (0 <= end_d <= end_d_data):
            # The days are in proper range
            start_d = start_d if start_d != 0 else 1
            # Selected last day of month for end day if it's not set
            end_d = end_d if end_d != 0 else end_d_data
        else:
            raise CalendarQueryException(
                f' "{start_d}" or "{end_d}" is not a valid month day'
                f'parameter. Range start month "{start_m}" has '
                f'"{start_d_data}" days and range end month "{end_m}" '
                f'has "{end_d_data}" For start range use "0" to select '
                f'first day of month and for range end use "0" to select '
                f'last day of month !')
        calendar = calendar.filter(
            getattr(Calendar, f'{caltype}_sn').between(
                int(f'{start_y}{start_m:02d}{start_d:02d}'),
                int(f'{end_y}{end_m:02d}{end_d:02d}'
                    )
                )
            )
    else:
        if start[0] != 0:
            calendar = calendar.where(
                getattr(Calendar, f'{caltype}_year') == start[0]
                )
        if start[1] > 0 and start[1] <= 12:
            calendar = calendar.where(
                getattr(Calendar, f'{caltype}_month') == start[1]
                )
        else:
            if start[1] != 0:
                raise CalendarQueryException(
                    f' "{start[1]}" is not a valid month parameter. '
                    f'Use "0" to select all months or use anything '
                    f'between "1" and "12" !')
        day_in_month = 31
        if start[1] != 0:
            day_in_month = get_days_on(
                caltype=caltype, year=start[0], month=start[1]
                )
        if start[2] > 0 and start[2] <= day_in_month:
            calendar = calendar.where(
                getattr(Calendar, f'{caltype}_day') == start[2]
                )
        else:
            if start[2] != 0:
                raise CalendarQueryException(
                    f' "{start[2]}" is not a valid day parameter. '
                    f'Use "0" to select all days or use anything '
                    f'between "1" and "{day_in_month}" for the month!'
                    )
    if only_holidays:
        calendar = calendar.filter(Calendar.is_holiday == 1)
    if except_holidays:
        calendar = calendar.filter(Calendar.is_holiday == 0)
    if len(filter_tithis) > 0:
        calendar = calendar.filter(
            Events.event_class == 'tithi', Events.event_name.in_(filter_tithis)
            )
    if search_event.strip() != '':
        calendar = calendar.filter(Events.event_name.like(search_event))
    return calendar


def calender_result_to_dict(calendar_days, bs_as_key: bool = False):
    data: dict = {}
    for date in calendar_days:
        yyyy: str = str(
            getattr(
                date[0],
                f'{"bs" if bs_as_key else "ad"}_year'
                )
            )
        mm: str = str(
            getattr(
                date[0],
                f'{"bs" if bs_as_key else "ad"}_month'
                )
            )
        if yyyy not in data:
            data[yyyy] = {}
        if mm not in data[yyyy]:
            data[yyyy][mm] = {}
        dd: str = str(
            getattr(
                date[0],
                f'{"bs" if bs_as_key else "ad"}_day'
                )
            )

        data[yyyy][mm][dd] = {
            'tithi': '',
            'event': [],
            'panchangam': [],
            'date': {
                'ad': {
                    'year': date[0].ad_year,
                    'month': date[0].ad_month,
                    'day': date[0].ad_day,
                },
                'bs': {
                    'year': date[0].bs_year,
                    'month': date[0].bs_month,
                    'day': date[0].bs_day,
                },
            },
            'public_holiday': date[0].is_holiday
        }
        for relation in date[0].CalendarEventRelationship:
            if relation.events.event_class == 'tithi':
                data[yyyy][mm][dd]['tithi'] = relation.events.event_name
            else:
                data[yyyy][mm][dd][relation.events.event_class].append(
                    relation.events.event_name
                    )
    return data


@app.route('/v2/date/<string:caltype>/<string:date>')
def date_view(caltype: str, date: str):
    today = get_today(caltype=caltype)
    try:
        s_date = [
            int(chunk)
            for chunk in
            calendar_var_replace(caltype=caltype, string=date).split('-')
            if chunk.strip() != ''
            ]
    except ValueError:
        return {
            'error': 'Invalid start date format ! Supported format: "yyyy-m-d"'
                }, 400
    try:
        calendar = calender_query_builder(
            caltype=caltype.lower(),
            start=(
                s_date[0],
                s_date[1] if len(s_date) >= 2 else 0,
                s_date[2] if len(s_date) >= 3 else 0
                ),
            only_holidays=bool(
                int(
                    request.args.get(
                        'only_holidays', 0
                        )
                    )
                ),
            except_holidays=bool(
                int(request.args.get('except_holidays', 0))
                ),
            filter_tithis=request.args.get(
                'filter_tithis', ''
                ).split(';'),
            search_event=request.args.get(
                'search', '')
                )
        calendar_days = db.session.execute(calendar).all()
        if len(calendar_days) == 0:
            return {'error': 'No data found for date !'}, 404
        return calender_result_to_dict(
            calendar_days=calendar_days,
            bs_as_key=bool(
                int(
                    request.args.get(
                        'bs_as_key', 0
                        )
                    )
                )
            )
    except CalendarQueryException as e:
        return {'error': str(e)}, 500


@app.route('/v2/range/<string:caltype>/from/<string:sdate>/to/<string:edate>')
def range(caltype: str, sdate: str, edate: str):
    today = get_today(caltype=caltype)
    try:
        s_date = [
            int(chunk)
            for chunk in
            calendar_var_replace(caltype=caltype, string=sdate).split('-')
            if chunk.strip() != ''
            ]
    except ValueError:
        return {
            'error': 'Invalid start date format ! Supported format: "yyyy-m-d"'
                }, 400
    try:
        e_date = [
            int(chunk)
            for chunk in
            calendar_var_replace(caltype=caltype, string=edate).split('-')
            if chunk.strip() != ''
            ]
    except ValueError:
        return {
            'error': 'Invalid end date format ! Supported format: "yyyy-m-d"'
                }, 400
    try:
        calendar = calender_query_builder(
            caltype=caltype.lower(),
            start=(
                s_date[0],
                s_date[1] if len(s_date) >= 2 else 0,
                s_date[2] if len(s_date) >= 3 else 0
                ),
            end=(
                e_date[0],
                e_date[1] if len(e_date) >= 2 else 0,
                e_date[2] if len(e_date) >= 3 else 0
                ),
            only_holidays=bool(
                int(
                    request.args.get(
                        'only_holidays', 0
                        )
                    )
                ),
            except_holidays=bool(
                int(
                    request.args.get(
                        'except_holidays', 0
                        )
                    )
                ),
            filter_tithis=request.args.get(
                'filter_tithis', ''
                ).split(';'),
            search_event=request.args.get(
                'search', ''
                )
            )
        calendar_days = db.session.execute(calendar).all()
        if len(calendar_days) == 0:
            return {'error': 'No data found for date !'}, 404
        return calender_result_to_dict(
            calendar_days=calendar_days,
            bs_as_key=bool(
                int(
                    request.args.get(
                        'bs_as_key', 0
                        )
                    )
                )
            )
    except CalendarQueryException as e:
        return {'error': str(e)}, 400


@app.route('/v2/@today')
def today():
    dtn = datetime.now()
    return redirect(
        url_for(
            'date_view',
            caltype='ad',
            date=f'{dtn.year}-{dtn.month}-{dtn.day}'
            ) + '?' + request.query_string.decode(), 302)


@app.route('/v1/<string:opmode>')
def old_date_view(opmode: str):
    calendar_type = request.args.get('calendar', 'ad').lower()
    if calendar_type not in ['ad', 'bs']:
        return {'error': 'Invalid calendar type ! Use "ad", or "bs"'}
    query_string = request.query_string.decode()\
        .replace(f'calendar={request.args.get("calendar")}', '')\
        .replace(f'date={request.args.get("date")}', '')\
        .replace(f'start_date={request.args.get("start_date")}', '')\
        .replace(f'end_date={request.args.get("end_date")}', '')
    if opmode == 'date':
        return redirect(
            url_for(
                'date_view',
                caltype=calendar_type,
                date=request.args.get("date")
                ) + '?' + query_string, 309)
    elif opmode == 'range':
        return redirect(
            url_for(
                'range',
                caltype=calendar_type,
                sdate=request.args.get('start_date'),
                edate=request.args.get('end_date')
                ) + '?' + query_string, 309)
    else:
        return {'error': 'Invalid operation mode !'}, 400


if __name__ == '__main__':
    artifacts_dir = os.listdir(os.path.join(os.path.dirname(__name__), 'artifacts'))
    with app.app_context():
        db.create_all()
        available_years = sorted([
            int(file.replace('.json', '').replace('artifact-', ''))
            for file in artifacts_dir
            if
            file.startswith('artifact-') and file.endswith('.json')
            ])
        print(f'[I] Artifacts found for years:  {", ".join(year for year in available_years)} ')
        for year in available_years:
            if int(os.environ.get('SKIP_DB_CREATE', 0)):
                break
            with open(f'artifact-{year}.json', 'r') as cf:
                cal = json.load(cf)
            for eng_date in cal:
                ENG_YEAR: int = int(
                    eng_date.split('/')[0]
                    )
                ENG_MONTH: int = int(
                    eng_date.split('/')[1]
                    )
                ENG_DAY: int = int(
                    eng_date.split('/')[2]
                    )

                NEP_YEAR: int = int(
                    cal[eng_date]['nepali_date'].split('/')[0]
                    )
                NEP_MONTH: int = int(
                    cal[eng_date]['nepali_date'].split('/')[1]
                    )
                NEP_DAY: int = int(
                    cal[eng_date]['nepali_date'].split('/')[2]
                    )

                _calendar = db.session.execute(
                    db.select(Calendar).filter_by(
                        ad_sn=int(f'{ENG_YEAR}{ENG_MONTH:02d}{ENG_DAY:02d}'),
                        bs_sn=int(f'{NEP_YEAR}{NEP_MONTH:02d}{NEP_DAY:02d}'),
                        ad_year=ENG_YEAR, ad_month=ENG_MONTH, ad_day=ENG_DAY,
                        bs_year=NEP_YEAR, bs_month=NEP_MONTH, bs_day=NEP_DAY)
                    ).first()
                calendar = None
                if _calendar is None:
                    calendar = Calendar(
                        ad_sn=int(f'{ENG_YEAR}{ENG_MONTH:02d}{ENG_DAY:02d}'),
                        bs_sn=int(f'{NEP_YEAR}{NEP_MONTH:02d}{NEP_DAY:02d}'),
                        ad_year=ENG_YEAR, ad_month=ENG_MONTH, ad_day=ENG_DAY,
                        bs_year=NEP_YEAR, bs_month=NEP_MONTH, bs_day=NEP_DAY,
                        is_holiday=cal[eng_date]['is_public_holiday']
                        )
                    db.session.add(calendar)
                    db.session.flush()
                else:
                    calendar = _calendar[0]
                cal_events: list[tuple] = []
                inserted_p_keys = []
                # Collect all the events
                cal_events.append((cal[eng_date]['tithi'], 'tithi'))
                for event in cal[eng_date]['events']:
                    if event != '':
                        cal_events.append((event, 'event'))
                for event in cal[eng_date]['panchangam']:
                    if event != '':
                        cal_events.append((event, 'panchangam'))

                inserted_events: list[db.Model] = []
                # Add them to database
                for event in cal_events:
                    exec = db.session.execute(
                        db.select(Events).filter_by(
                            event_name=event[0], event_class=event[1]
                            )
                        ).first()
                    if exec is None:
                        # Add event, it does not exist rn
                        inserted_events.append(
                            Events(
                                event_name=event[0], event_class=event[1]
                                )
                            )
                        db.session.add(inserted_events[-1])
                    else:
                        inserted_p_keys.append(exec[0].id)
                db.session.flush()

                for added_event in inserted_events:
                    inserted_p_keys.append(added_event.id)
                # Calander and events are now added, now build relations
                for id in inserted_p_keys:
                    ev = db.session.execute(
                        db.select(CalendarEventRelationship).filter_by(
                            day_id=calendar.id, event_id=id
                            )
                        ).first()
                    if ev is None:
                        db.session.add(
                            CalendarEventRelationship(
                                day_id=calendar.id, event_id=id
                                )
                            )
                print(
                    f'[I] Added date for year  {eng_date} '
                    f'<-> {NEP_YEAR}/{NEP_MONTH}/{NEP_DAY}'
                    )
        db.session.commit()
    app.run(host=os.environ.get('HOST', '0.0.0.0'), port=os.environ.get('PORT', '8080'), debug=int(os.environ.get('DEBUG', 0)))
