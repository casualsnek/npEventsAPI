# npEventsAPI
API and data for nepali holidays and calendar events

Currently, it can
- Build 'kholidays' holiday definition file allowing you to get event information natively in KDE plasma desktop
- Create an HTTP API with python flask, allowing filtering, searching and a few other complex queries

## Usage
Before using the tool in any way, setup python environment and GIT in your system.
After setting up python and GIT, open a console and run the following commands
```bash
git clone https://github.com/casualsnek/npEventsAPI
cd ./npEventsAPI
python -m pip install -r requirements.txt
```

### 1. Create/Update JSON artifacts 
Fork this repo, then add or modify the artifact for year you are interested in ```./artifacts``` directory.
Artifact file should be named as 'artifact-{YEAR_IN_BS}.json'
After you have added a new year or made changes to the existing files, submit a Pull Request to this repo


### 2. Create 'kholiday' holiday definition file
Generating holiday definition requires artifact to be already generated.
The tool will use artifact provided to generate ```kholiday_np_np@.*``` files which you can put into kholiday library's source,
compile it and install to get different classes Nepali events as holiday in calendar widget.
(You need to enable and restart your desktop session to get events displayed).
Refer to [this URL](https://invent.kde.org/frameworks/kholidays/-/tree/master/) for instruction
on how to build the kholiday library by yourself and where to put the generated definitions.

Generate holiday file by running the following commands
```bash
python utils.py -k -ia artifact-2080.json -hod ./holiday -se holidays,nepali_date= -fh -ah
```
This will create a holiday definition under ```holiday``` directory located in current directory.
The definition will contain Nepali Public holidays and Nepali Dates in BS as holiday event for calendar.
Selecting Nepali dates to be visible as holiday will allow you to check today's date in BS.
Directly in your calendar.

| Argument  | Description   |
|---|---|---|
| -k | Switch to kholiday generation mode |
| -ia | Input artifact, the ones generated in **1.1**.
You can pass it multiple times to add events for multiple years |
| -hod | Path to directory where the generated file will be placed |
| -se | Selected events.
Events that will show up as holiday in the calendar.
Available options: ```holidays, nepali_date, panchangam, tithi, non_holiday_events```.
Separated by comma without space between them
| -fh | Flatten holiday.
Squash all holidays for a day into single string so that they all appear as one single event in calendar |
| -ah | Append ```सार्बजनिक बिदा:``` in front of names of events in public holidays |
| -ap | Append ```पञ्चाङ्ग:``` in front of names of Panchangam events in if the event is selected |

### 3. Serve HTTP API
Serving the data as HTTP API requires you to generate artifacts first as shown in **1.1** .
Place the generated artifacts in the same directory as ```flask_api.py``` and run the following command on console:
```bash
python __main__.py
```
The available environment variables while starting API are :
| ENV Var  | Value | Default value | Description   |
|---|---|---|---|
| DEBUG | 1/0 | 0 | Enables or Disables flask debugging mode |
| HOST | IP Address | 0.0.0.0 | Host on which to listen for connections |
| PORT | IP Address | 8080 | Port on which to listen for connections |
| PORT | Integer | 8080 | Port on which to listen for connections |
| SKIP_DB_CREATE | 1/0 | 0 | If set to 1 skips the process that puts artifacts in the database.
Set this to 1 if you have already run the application at least once.

### 4 HTTP API Documentation
The npEventsAPI HTTP API provides a way to query Nepali calendar events via HTTP web requests.
In the following API documentation all the ```date``` type variable are in ```yyyy-m-d``` format such as ```2022-2-14```.
The ```caltype``` variable is type of calendar that is being used for dates in API calls.
It is always either ```ad``` or ```bs```.

#### 4.1  Date Endpoint: ```/v2/date/<caltype>/<date>```
**Description**: This endpoint provides data(s) about a particular date like year, month and day.
It can be used to get information about months, day of months, years and so on.
**Arguments:**

-  ```<caltype>```: Type of calendar system being used for the date in API call
- ```<date>```: Date to query for in the format ```yyyy-m-d```

**Sample response**: Call to ```http://127.0.0.1:8080/v2/date/ad/2023-5-15```

```json
{
  "2023": {
    "5": {
      "15": {
        "date": {
          "ad": {
            "day": 15,
            "month": 5,
            "year": 2023
          },
          "bs": {
            "day": 1,
            "month": 2,
            "year": 2080
          }
        },
        "event": [
          "अपरा एकादशी व्रत",
          "वृष संक्रान्ति",
          "अन्तर्राष्ट्रिय परिवार दिवस",
          "चित्तधर हृदय जन्म जयन्ती"
        ],
        "panchangam": [
          "जेठ कृष्ण एकादशी",
          "विषकुम्भ बव पूर्वभाद्र"
        ],
        "public_holiday": false,
        "tithi": "एकादशी"
      }
    }
  }
}
```

 **Notes:** Using '0' as value in any position of the date format ignores the part of date and does the further queries.
**The calendar system used in the following statements are in ```ad```**

- Call to API with date as ```2022-11-12``` with give you the information about 12th of November 2022.
- Call to API with date as ```2022-11-0``` with give you the information about 12th of every month and every day of 2022, the date can also be simply written as ```2022-11```.
- Call to API with date as ```2022-0-0``` with give you the information about every day of every month in 2022, the date can also be simply written as ```2022```.
-  Call to API with date as ```0-11-12``` with give you the information about 12th of November from every year that exists in the database
- Call to API with date as ```0-0-12``` with give you the information about 12th of every month of every year that exists in the database.
-  Call to API with date as ```2022-0-12``` with give you the information about 12th of every month of year 2022.

#### 4.2  Range Endpoint: ```/v2/range/<caltype>/from/<date>/to/<date>```
**Description**: This endpoint is almost same as the ```date``` endpoint except that you can select particular date range to pick event from rather than getting information about whole year, month, or day. The date after ```/from``` is the start of range and the date after ```/to``` is the end date. Unlike ```date``` endpoint all the parts of date format ```yyyy-m-d``` must be filled for both from and to date.

In case of ```/from/<date>``` if any of ```m``` or ```d``` part of ```yyyy-m-d``` is left blank or set to 0.
Month will default to ```1``` and day will also default to ```1```.
So, ```/from/2022-0-0``` or ```/from/2022``` is equivalent to ```/from/2022-1-1```.

But, In case of ```/to/<date>``` if any of ```m``` or ```d``` part of ```yyyy-m-d``` is left blank or set to 0.
Month will default to last month  ```12``` and day will default to last day of month  ```30```.
So, ```/to/2022-0-0``` or ```/to/2022``` is equivalent to ```/from/2022-12-30```.

This API is useful to get, for example, event of the next 15 days to calculate the number of holidays within the range.

**Arguments:**

-  ```<caltype>```: Type of calendar system being used for the date in API call
- ```/from/<date>```: Date to start range for in the format ```yyyy-m-d```
- ```/to/<date>```: Date to end range for in the format ```yyyy-m-d```

**Notes:** 'from' date should always be older than 'to' date

**Sample response**: Call to ```http://127.0.0.1:8080/v2/range/ad/2023-5-15/2023-5-17```
```json
{
  "2023": {
    "5": {
      "15": {
        "date": {
          "ad": {
            "day": 15,
            "month": 5,
            "year": 2023
          },
          "bs": {
            "day": 1,
            "month": 2,
            "year": 2080
          }
        },
        "event": [
          "अपरा एकादशी व्रत",
          "वृष संक्रान्ति",
          "अन्तर्राष्ट्रिय परिवार दिवस",
          "चित्तधर हृदय जन्म जयन्ती"
        ],
        "panchangam": [
          "जेठ कृष्ण एकादशी",
          "विषकुम्भ बव पूर्वभाद्र"
        ],
        "public_holiday": false,
        "tithi": "एकादशी"
      },
      "16": {
        "date": {
          "ad": {
            "day": 16,
            "month": 5,
            "year": 2023
          },
          "bs": {
            "day": 2,
            "month": 2,
            "year": 2080
          }
        },
        "event": [],
        "panchangam": [
          "जेठ कृष्ण द्वादशी",
          "प्रीति कौलव उत्तरभाद्र"
        ],
        "public_holiday": false,
        "tithi": "द्वादशी"
      },
      "17": {
        "date": {
          "ad": {
            "day": 17,
            "month": 5,
            "year": 2023
          },
          "bs": {
            "day": 3,
            "month": 2,
            "year": 2080
          }
        },
        "event": [
          "प्रदोष व्रत",
          "विश्व दूरसञ्चार दिवस",
          "विश्व उच्च रक्तचाप दिवस"
        ],
        "panchangam": [
          "जेठ कृष्ण त्रयोदशी",
          "आयुष्मान गर रेवती"
        ],
        "public_holiday": false,
        "tithi": "त्रयोदशी"
      }
    }
  }
}
```
#### 4.3 Filters/searching and structures
For all endpoints, the returned data can be further filtered or organized by using available URL parameters.
The available parameters are as follows:
| Parameter | Description | Query URL example
|---|---|---|
| only_holidays | If set to ```1```, the data to be returned by API will only keep the days marked as public holidays, all other days will be removed from the result | ```http://127.0.0.1:8080/v2/date/bs/2080?only_holidays=1``` <br> This will return all days in year 2080 BS.
which are marked as public holiday.|
| except_holidays |  If set to ```1```, the data to be returned by API will only keep the days not marked as public holidays, all other days which are marked public holiday will be removed from the result | ```http://127.0.0.1:8080/v2/date/bs/2080?only_holidays=1``` <br> This will return all days in year 2080 BS.
Which is not marked as a public holiday.
|
| filter_tithis | Tithis seperated by ```;```,
This will filter out all the days from a result that are not on the given list of tithis.
| ```http://127.0.0.1:8080/v2/date/bs/2080?filter_tithis=त्रयोदशी;द्वादशी``` <Br> This will return all days in year 2080 BS.
Which are tithi is either 'त्रयोदशी' or 'द्वादशी' |
| search | A search term, this will search the result for search term and only return the days,
which has any event that matches search term.
|  ```http://127.0.0.1:8080/v2/date/bs/2080?search=अन्तर्राष्ट्रिय परिवार दिवस``` <Br> This will return all days in year 2080 BS.
Whose one of the events is 'अन्तर्राष्ट्रिय परिवार दिवस'?
|
| Bs_as_key | If this parameter is set to ```1```.
The keys in returned JSON will be in BS instead of AD | ```http://127.0.0.1:8080/v2/date/bs/2080-1-1?bs_as_key=1``` <br> <br> will return ```{"2080":{"1":{"1":{"date":{"ad":{"day":14,"month":4,"year":2023},"bs":{"day":1,"month":1,"year":2080}},"event":["नयाँ वर्ष","मेष संक्रान्ति","बिस्का: जात्रा"],"panchangam":["वैशाख कृष्ण नवमी","सिद्ध तैतल उत्तरषाढा"],"public_holiday":true,"tithi":"नवमी"}}}} ``` <br> <br>instead of ```{"2023":{"4":{"14":{"date":{"ad":{"day":14,"month":4,"year":2023},"bs":{"day":1,"month":1,"year":2080}},"event":["नयाँ वर्ष","मेष संक्रान्ति","बिस्का: जात्रा"],"panchangam":["वैशाख कृष्ण नवमी","सिद्ध तैतल उत्तरषाढा"],"public_holiday":true,"tithi":"नवमी"}}}}```|

**Note:** Any of the parameter combinations can be mixed and used in any API to get the result you need

### 4.4 Variables
There are a few variables that you can use within the ```<date>``` type parameter instead of numeric values.
The variable's values will be automatically adjusted on server depending on the ```<caltype>``` you are using.
Some of the available variables are:
The examples below consider today's date to be ```2023-5-16```

- **```@today```** :  This variable will be automatically interpreted as today's full date. It is equivalent to valid date string like ```2023-5-16```
- **```@cur_year```** : This variable will be automatically interpreted as the current year. In a date string ```@cur_year-5-16``` is same as ```2023-5-16```
- **```@cur_month```** : This variable will be automatically interpreted as the current month. In a date string ```2022-@cur_month-16``` is same as ```2023-5-16```
- **```@cur_day```** : This variable will be automatically interpreted as the current day. In a date string ```2022-5-@cur_day``` is same as ```2023-5-16```

## And this is it!
Help improve this repository by **reporting bugs**,
**improving code/documentation**, **sharing the words** and **using it**.
If you have any queries, feel free to open a new issue!

