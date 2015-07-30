import api.views
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
import uqx_api.courses
from collections import OrderedDict
import pycountry
import urllib2
import json
from datetime import date, datetime, timedelta
from api.models import UserEnrol, CourseProfile, UserCertificate, PersonCourse, Ingestor, CourseEvent
import dateutil
from rest_framework.permissions import AllowAny
import config

from django.db import models

# Logging
import logging
logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes((AllowAny, ))
def meta_courses(request):
    """
    Lists the course information, in particular the course ID
    """
    if api.views.is_cached(request):
        return api.views.api_cacherender(request)
    courses = []
    for db in uqx_api.courses.EDX_DATABASES:
        if db == 'default' or db == 'personcourse' or db == 'Course_Event':
            continue

        course = OrderedDict()
        course['id'] = db
        course['name'] = str(db).replace('_', ' ')
        course['icon'] = uqx_api.courses.EDX_DATABASES[db]['icon']
        course['year'] = uqx_api.courses.EDX_DATABASES[db]['year']
        courses.append(course)
    courses = sorted(courses, key=lambda k: k['year'])
    data = courses
    return api.views.api_render(request, data, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def meta_courseinfo(request):
    """
    Lists the course information, in particular the course ID with extra information
    """
    if api.views.is_cached(request):
        return api.views.api_cacherender(request)
    courses = []
    for db in uqx_api.courses.EDX_DATABASES:
        if db == 'default' or db == 'personcourse' or db == 'Course_Event':
            continue

        course = OrderedDict()
        course['id'] = db
        course['name'] = str(db).replace('_', ' ')
        course['icon'] = uqx_api.courses.EDX_DATABASES[db]['icon']
        course['year'] = uqx_api.courses.EDX_DATABASES[db]['year']

        coursedb = api.views.get_course(course['id'])

        filename = uqx_api.courses.EDX_DATABASES[db]['discussiontable'].replace("/", "-").replace("-prod", "")
        courseurl = config.SERVER_URL + '/datasources/course_structure/'+filename+'.json';
        data = '[]'
        try:
            data = urllib2.urlopen(courseurl).read().replace('<script','').replace('</script>','')
            try:
                data = json.loads(data)
                max_per_day_date = datetime.now()
                if 'end' in data:
                    course['end'] = data['end']
                    course['end'] = str(str(course['end']).replace('+00:00', 'Z')).replace('"', "")
                if 'start' in data:
                    course['start'] = data['start']
                    course['start'] = str(str(course['start']).replace('+00:00', 'Z')).replace('"', "")
                    max_per_day_date = dateutil.parser.parse(course['start']) + timedelta(days=7)
                if 'start' in data and 'end' not in data:
                    course['end'] = course['start']
                if 'display_name' in data:
                    course['display_name'] = data['display_name']
                max_per_day_date = max_per_day_date.replace(tzinfo=None)
                total = 0
                within_per_day = 0
                certificates = 0
                duringcourse = 0
                first_date = datetime.now()
                for user in UserEnrol.objects.using(db).all():
                    userdate = user.created.replace(tzinfo=None)
                    if first_date > userdate:
                        first_date = userdate
                    if userdate < max_per_day_date:
                        within_per_day += 1
                    total += 1
                    certificates += 1
                    if userdate < course['end']:
                        duringcourse += 1

                certificates = len(UserCertificate.objects.using(db).filter(status='downloadable'))

                range = (max_per_day_date - first_date).days

                per_day = round(within_per_day/range, 2)

                course['enrolments'] = total
                course['enrolments_per_day'] = per_day
                course['certificates'] = certificates
                course['enroled_during_course'] = duringcourse
                courses.append(course)
            except Exception as e:
                print "COULDNT PARSE COURSE DATA FOR "+course['id']
                logger.info("COULDNT PARSE COURSE DATA FOR "+course['id'])
                logger.info("COURSE URL: "+str(courseurl))
                logger.info(e)
                print data
                pass
        except Exception as e:
            print "COULDNT PARSE COURSE "+course['id']
            logger.info("COULDNT PARSE COURSE "+course['id'])
            logger.info("COURSE URL: "+str(courseurl))
            logger.info(e)
            pass
    data = courses
    return api.views.api_render(request, data, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def meta_uniques(request):
    """
    The number of unique students for UQx courses
    """
    if api.views.is_cached(request):
        return api.views.api_cacherender(request)
    users = []
    total = 0
    for db in uqx_api.courses.EDX_DATABASES:
        if db == 'default' or db == 'personcourse' or db == 'Course_Event':
            continue

        for user in UserEnrol.objects.using(db).all():
            total += 1
            if user.user_id not in users:
                users.append(user.user_id)
    data = OrderedDict()
    data['uniques'] = len(users)
    data['total'] = total
    return api.views.api_render(request, data, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def meta_countries(request):
    """
    Lists the country codes and names
    """
    if api.views.is_cached(request):
        return api.views.api_cacherender(request)
    countries = list(pycountry.countries)
    data = OrderedDict()
    for country in countries:
        data[country.alpha2] = country.name
    return api.views.api_render(request, data, status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((AllowAny, ))
def meta_modes(request):
    """
    Lists the modes of enrolment
    """
    if api.views.is_cached(request):
        return api.views.api_cacherender(request)
    data = OrderedDict()
    data['blank'] = {'name': 'blank', 'description': ''}
    data['audit'] = {'name': 'audit', 'description': ''}
    data['honor'] = {'name': 'honor', 'description': ''}
    data['verified'] = {'name': 'verified', 'description': ''}
    return api.views.api_render(request, data, status.HTTP_200_OK)


@api_view(['GET'])
def meta_structure(request, course_id=''):

    """
    Returns a nested structure of the course structure for an edX course
    """
    if course_id is '':
        return api.views.api_render(request, {'error': 'Must supply a course ID'}, status.HTTP_400_BAD_REQUEST)
    if api.views.is_cached(request):
        return api.views.api_cacherender(request)

    course = api.views.get_course(course_id)
    if course is None:
        return api.views.api_render(request, {'error': 'Unknown course code'}, status.HTTP_404_NOT_FOUND)

    filename = course['discussiontable'].replace("/", "-").replace("-prod", "")
    courseurl = config.SERVER_URL + '/datasources/course_structure/'+filename+'.json'
    data = '[]'
    try:
        data = urllib2.urlopen(courseurl).read().replace('<script', '').replace('</script>', '')
    except:
        return api.views.api_render(request, {'error': 'Could not find course file: Looking for '+str(courseurl)}, status.HTTP_404_NOT_FOUND)
    print courseurl
    data = json.loads(data)
    return api.views.api_render(request, data, status.HTTP_200_OK)

@api_view(['GET'])
def meta_courseprofile(request, course_id='all'):
    """
    Returns derived course profiles for a course
    """
    if api.views.is_cached(request):
        return api.views.api_cacherender(request)
    courses = []
    if course_id is 'all':
        courselist = api.views.get_all_courses()
        for course in courselist:
            courses.append(courselist[course]['id'])
        pass
    else:
        course = api.views.get_course(course_id)
        if course is None:
            return api.views.api_render(request, {'error': 'Unknown course code'}, status.HTTP_404_NOT_FOUND)
        courses.append(course['id'])

    data = {}

    for course in courses:
        data[course] = {}
        course_data = CourseProfile.objects.using("personcourse").filter(course=course)
        if len(course_data) > 0:
            data[course] = course_data[0].to_dict(None)
            data[course]['status'] = 'available'
        else:
            data[course]['status'] = 'unavailable'

    return api.views.api_render(request, data, status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((AllowAny, ))
def meta_enrolcount(request, course_id='all'):
    """
    Returns the enrolment count over the last week
    """
    if api.views.is_cached(request):
        return api.views.api_cacherender(request)
    data = OrderedDict()

    courses = []
    if course_id is 'all':
        courselist = api.views.get_all_courses()
        for course in courselist:
            courses.append(courselist[course]['id'])
        pass
    else:
        course = api.views.get_course(course_id)
        if course is None:
            return api.views.api_render(request, {'error': 'Unknown course code'}, status.HTTP_404_NOT_FOUND)
        courses.append(course_id)

    day_students = 0
    week_students = 0
    month_students = 0

    for course in courses:

        last_date = None
        PersonCourse._meta.db_table = 'personcourse_'+course
        if api.views.db_table_exists("personcourse",PersonCourse._meta.db_table):
            for table_user in PersonCourse.objects.using("personcourse").all():
                if table_user.start_time is not None:
                    if last_date is None or table_user.start_time > last_date:
                        last_date = table_user.start_time

        if last_date is not None:

            month_ago = last_date + timedelta(-30)
            week_ago = last_date + timedelta(-7)
            day_ago = last_date + timedelta(-1)

            PersonCourse._meta.db_table = 'personcourse_'+course
            for table_user in PersonCourse.objects.using("personcourse").all():
                if table_user.start_time is not None:
                    if table_user.start_time > month_ago:
                        month_students += 1
                        if table_user.start_time > week_ago:
                            week_students += 1
                            if table_user.start_time > day_ago:
                                day_students += 1

    data['last_week'] = str(week_students)
    data['last_month'] = str(month_students)
    data['last_day'] = str(day_students)

    return api.views.api_render(request, data, status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((AllowAny, ))
def meta_lastingest(request):
    """
    Returns the last time the ingested data was run, and the latest date that the ingestion data was supplied
    """
    ingests = get_latest_ingest_dates()

    return api.views.api_render(request, ingests, status.HTTP_200_OK)

def get_latest_ingest_dates():
    last_ingested_item = None
    last_clicksteam_item_date = None
    for ingest in Ingestor.objects.using("default").all():
        #if ingest.completed_date:
        if ingest.completed == 1 and ingest.completed_date:
            if last_ingested_item is None or ingest.completed_date > last_ingested_item.completed_date:
                last_ingested_item = ingest
            if ingest.service_name == 'Clickstream':
                click_date = ingest.meta.replace(".log", "")
                click_date = datetime.strptime(click_date[-10:], "%Y-%m-%d")
                if last_clicksteam_item_date is None or click_date > last_clicksteam_item_date:
                    last_clicksteam_item_date = click_date

    data = OrderedDict()
    data['ingest_date'] = datetime.strftime(last_ingested_item.completed_date, "%Y-%m-%d")
    data['data_date'] = datetime.strftime(last_clicksteam_item_date, "%Y-%m-%d")
    return data

@api_view(['GET'])
@permission_classes((AllowAny, ))
def meta_ingeststatus(request):
    """
    Returns the current information on the ingestion process
    """
    ingestions = {}

    for ingest in Ingestor.objects.using("default").all():
        if ingest.service_name not in ingestions:
            ingestions[ingest.service_name] = {
                'total': 0,
                'remaining': 0,
                'current': '',
                'completed': 0,
                'last_ingest_date': None,
                'current_start': None
            }
        if ingest.completed == 1 and ingest.completed_date:
            ingestions[ingest.service_name]['completed'] += 1
            if ingestions[ingest.service_name]['last_ingest_date'] is None or ingest.completed_date > ingestions[ingest.service_name]['last_ingest_date'].completed_date:
                ingestions[ingest.service_name]['last_ingest_date'] = ingest
        else:
            ingestions[ingest.service_name]['remaining'] += 1
        if ingest.completed == 0 and ingest.started == 1:
            ingestions[ingest.service_name]['current'] = ingest.meta
            if ingest.started_date is not None:
                ingestions[ingest.service_name]['current_start'] = datetime.strftime(ingest.started_date, "%Y-%m-%d %H:%M:%S")
        ingestions[ingest.service_name]['total'] += 1

    for ingest in ingestions:
        if ingestions[ingest]['last_ingest_date'] is not None:
            ingestions[ingest]['last_ingest_date'] = datetime.strftime(ingestions[ingest]['last_ingest_date'].completed_date, "%Y-%m-%d %H:%M:%S")

    return api.views.api_render(request, ingestions, status.HTTP_200_OK)

@api_view(['GET'])
def meta_courseevents(request, course_id='all'):
    """
    Returns the data of course events
    """
    if api.views.is_cached(request):
        return api.views.api_cacherender(request)
    if course_id is 'all':
        return api.views.api_render(request, {'error': 'Unknown course code'}, status.HTTP_404_NOT_FOUND)
    else:
        course = api.views.get_course(course_id)
        if course is None:
            return api.views.api_render(request, {'error': 'Unknown course code'}, status.HTTP_404_NOT_FOUND)
    print course

    # Reading course_start from course info
    course_start = None
    filename = course['discussiontable'].replace("/", "-").replace("-prod", "")
    courseurl = config.SERVER_URL + '/datasources/course_structure/'+filename+'.json'
    try:
        courseinfo = urllib2.urlopen(courseurl).read().replace('<script', '').replace('</script>', '')
        courseinfo = json.loads(courseinfo)
        if 'start' in courseinfo:
            course_start = courseinfo['start']
            print course_start
    except Exception as e:
        print "COULDNT PARSE COURSE "+course['id']
        logger.info("COULDNT PARSE COURSE "+course['id'])
        logger.info("COURSE URL: "+str(courseurl))
        logger.info(e)
        pass
    course_start = datetime.strptime(course_start[:19], '%Y-%m-%dT%H:%M:%S').date()

    #
    db_name = 'Course_Event'
    app_label = 'courseevent'
    table_name = course['id']

    ce = CourseEvent(db_name, app_label + '_' + table_name, course_start)
    data = ce.counts_group_by_week()

    """
    # Dynamic Model
    model = create_model(table_name, fields,
    app_label=app_label,
    module=db_name+'.'+app_label+'.'+table_name,)

    # Get the end date of events
    end_record = model.objects.using(db_name).order_by('-event_date')[0]
    end_date = end_record.event_date
    """
    return api.views.api_render(request, data, status.HTTP_200_OK)
