from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import sys
from datetime import timedelta
from uqx_api import settings
from rest_framework.permissions import AllowAny

# APIs
from rest_framework.response import Response
from rest_framework.reverse import reverse

# Endpoints
from api.apis.meta import *
from api.apis.students import *
from api.apis.discussions import *
from api.apis.downloads import *
from api.apis.videos import *
from api.apis.person import *

# Logging
import logging
logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(('GET',))
@permission_classes((AllowAny, ))
def api_index(request, theformat=None):
    """
    Lists the currently available API endpoints.
    """
    endpointlist = OrderedDict()
    the_endpoints = endpoints()
    for endpoint_key in the_endpoints:
        firstlevel = str(endpoint_key).split('_')[0]
        if firstlevel not in endpointlist:
            endpointlist[firstlevel] = OrderedDict()
        endpoint = the_endpoints[endpoint_key]
        if 'requirevar' not in endpoint or 'requirevar' == False:
            endpointlist[firstlevel][endpoint['path']] = reverse(endpoint_key, request=request, format=theformat)
        if "option" in endpoint:
            optionname = "<"+endpoint['option']+">"
            endpointlist[firstlevel][endpoint['path']+"/"+optionname] = reverse(endpoint_key+"_"+endpoint['option'], request=request, format=theformat, kwargs={endpoint['option']: ''+endpoint['option']})
            pass
    return Response(endpointlist)


@csrf_exempt
@api_view(('GET',))
@permission_classes((AllowAny, ))
def endpointlist(request, theformat=None):
    """
    Lists the currently available API endpoints.
    """
    courses = []
    for db in uqx_api.courses.EDX_DATABASES:
        if db == 'default' or db == 'personcourse' or db == 'Course_Event':
            continue
        courses.append(db)
    endpointlist = OrderedDict()
    the_endpoints = endpoints()
    for endpoint_key in the_endpoints:
        endpoint = the_endpoints[endpoint_key]
        if 'requirevar' not in endpoint or 'requirevar' == False:
            endpointlist[endpoint['path']] = {
                'url': reverse(endpoint_key, request=request, format=theformat),
                'lastcache': cache_get_time("/api/"+endpoint['path']),
                'status': 'refresh'
            }
        if "option" in endpoint:
            if endpoint['option'] == 'course_id':
                for course in courses:
                    optionname = course
                    endpointlist[endpoint['path']+"/"+optionname] = {
                        'url': reverse(endpoint_key+"_"+endpoint['option'], request=request, format=theformat, kwargs={endpoint['option']: ''+optionname}),
                        'lastcache': cache_get_time("/api/"+endpoint['path']+"/"+optionname),
                        'status': 'refresh'
                    }
            pass
    return Response(endpointlist)


# The list of endpoints available
def endpoints():
    points = OrderedDict()

    points['student_genders'] = {'path': 'students/genders', 'option': 'course_id'}
    points['student_ages'] = {'path': 'students/ages', 'option': 'course_id'}
    points['student_fullages'] = {'path': 'students/fullages', 'option': 'course_id'}
    points['student_educations'] = {'path': 'students/educations', 'option': 'course_id'}
    points['student_countries'] = {'path': 'students/countries', 'option': 'course_id'}
    points['student_aus'] = {'path': 'students/countries', 'option': 'course_id'}
    points['student_modes'] = {'path': 'students/modes', 'option': 'course_id'}
    points['student_dates'] = {'path': 'students/dates', 'option': 'course_id'}
    points['student_active'] = {'path': 'students/active', 'option': 'course_id'}
    #points['student_activity'] = {'path': 'students/student_activity', 'option': 'course_id', 'requirevar': True}
    points['student_personcourse'] = {'path': 'students/personcourse', 'option': 'course_id', 'requirevar': True}
    points['student_in_age_range'] = {'path': 'students/inagerange', 'option': 'course_id'}
    points['student_in_age_range_together'] = {'path': 'students/inagerangetogether'}

    #points['discussion_countries'] = {'path': 'discussions/countries', 'option': 'course_id'}
    points['discussion_dates'] = {'path': 'discussions/dates', 'option': 'course_id', 'requirevar': True}
    points['discussion_popular'] = {'path': 'discussions/popular', 'option': 'course_id'}
    points['discussion_top'] = {'path': 'discussions/top', 'option': 'course_id'}
    points['discussion_category'] = {'path': 'discussions/category', 'option': 'course_id', 'requirevar': True}

    points['download_os'] = {'path': 'downloads/os'}
    points['download_browsers'] = {'path': 'downloads/browsers'}
    points['download_countries'] = {'path': 'downloads/countries'}

    points['meta_courses'] = {'path': 'meta/courses'}
    points['meta_courseinfo'] = {'path': 'meta/courseinfo'}
    points['meta_uniques'] = {'path': 'meta/uniques'}
    points['meta_structure'] = {'path': 'meta/structure', 'option': 'course_id', 'requirevar': True}
    points['meta_countries'] = {'path': 'meta/countries'}
    points['meta_modes'] = {'path': 'meta/modes'}
    points['meta_courseevents'] = {'path': 'meta/courseevents', 'option': 'course_id', 'requirevar': True}
    points['meta_courseprofile'] = {'path': 'meta/courseprofile', 'option': 'course_id'}
    points['meta_enrolcount'] = {'path': 'meta/enrolcount'}
    points['meta_lastingest'] = {'path': 'meta/lastingest'}
    points['meta_ingeststatus'] = {'path': 'meta/ingeststatus'}

    points['videos_views'] = {'path': 'videos/views', 'option': 'course_id', 'requirevar': True}

    points['person_profile'] = {'path': 'person/profile', 'option': 'user_id', 'requirevar': True}
    points['person_lookup'] = {'path': 'person/lookup', 'option': 'details', 'requirevar': True}
    logger.info("Getting endpoints")
    return points

@api_view(('GET',))
def refresh_cache(request):
    response = {'refreshed': 'true'}
    the_endpoints = endpoints()
    virtual_request = request
    virtual_request.refreshcache = True
    basepath = request.path.replace("refresh_cache","")
    for endpoint in the_endpoints:
        #if endpoint == 'student_genders':
        if 'requirevar' not in endpoint or 'requirevar' is False:
            request.path = basepath + the_endpoints[endpoint]['path']
            getattr(sys.modules[__name__], endpoint)(virtual_request)
            break
        if "option" in the_endpoints[endpoint]:
            if the_endpoints[endpoint]['option'] == 'course_id':
                courses = get_all_courses()
                for course in courses:
                    request.path = basepath + the_endpoints[endpoint]['path']+"/"+course
                    getattr(sys.modules[__name__], endpoint)(virtual_request)
    response['cachetime'] = settings.CACHES['default']['TIMEOUT']
    now = datetime.now()
    response['nextrefresh'] = now + timedelta(0, settings.CACHES['default']['TIMEOUT'])
    return Response(response)

# Internal Methods (not endpoints)

def api_render(request, data, response_status=status.HTTP_200_OK):
    if not is_cached(request):
        cache_save(cache_path(request), data)
    return Response(data, response_status)


def api_cacherender(request):
    return api_render(request, cache_get(cache_path(request)), status.HTTP_200_OK)


def is_cached(request):
    if cache.get(cache_path(request)):
        if 'refreshcache' in request.QUERY_PARAMS or hasattr(request, 'refreshcache') and request.refreshcache:
            logger.info("Refreshing Cache")
            return False
        return True
    return False


def get_course(course_id):
    if course_id in uqx_api.courses.EDX_DATABASES:
        return uqx_api.courses.EDX_DATABASES[course_id]
    return None


def get_all_courses():
    courses = dict(uqx_api.courses.EDX_DATABASES)
    del courses['default']
    del courses['personcourse']
    del courses['Course_Event']
    del courses['googleanalytics']
    return courses


def cache_save(path, data):
    logger.info("Saving cache for path "+fixpath(path)+", times out in "+str(settings.CACHES['default']['TIMEOUT']))
    cache.set(fixpath(path), data, settings.CACHES['default']['TIMEOUT'])
    cache_update_time(path)
    pass

def cache_update_time(path):
    cache.set('expiry_'+fixpath(path), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), settings.CACHES['default']['TIMEOUT'])


def cache_get(path):
    logger.info("Retrieving cache for path "+fixpath(path)+", times out in "+str(settings.CACHES['default']['TIMEOUT']))
    return cache.get(fixpath(path))


def cache_get_time(path):
    logger.info("Retrieving cache expiry time for path "+fixpath(path))
    if cache.get('expiry_'+fixpath(path)):
        return cache.get('expiry_'+fixpath(path))
    else:
        return ""


def db_table_exists(db, table):
        from django.db import connections
        table_names = connections[db].introspection.get_table_list(connections[db].cursor())
        print table_names
        return table in table_names


def cache_path(request):
    get = ""
    for param in request.GET:
        print param
        if param != 'refreshcache' and param != 'format':
            paramval = request.GET[param]
            paramval = paramval.replace(" ", "").replace("%20", "")
            get += param+":"+paramval
    if get != "":
        get = "?"+get
    request_path = request.path.replace(" ", "").replace("%20", "")
    return str(fixpath(request_path+get))


def fixpath(path):
    return path.rstrip('\/')
