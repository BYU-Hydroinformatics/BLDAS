# Define your REST API endpoints here.
# In the comments below is an example.
# For more information, see:
# http://docs.tethysplatform.org/en/dev/tethys_sdk/rest_api.html
"""
from django.http import JsonResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def get_data(request):
    '''
    API Controller for getting data
    '''
    name = request.GET.get('name')
    data = {"name": name}
    return JsonResponse(data)
"""

from utils import get_point_stats,get_feature_stats,get_polygon_stats
from django.http import JsonResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes

def get_point_ts(request):
    json_obj = {}

    if request.method == 'GET':
        variable = None
        lat = None
        lon = None
        interval = None
        year = None

        if request.GET.get('lat'):
            lat = request.GET['lat']

        if request.GET.get('lon'):
            lon = request.GET['lon']

        if request.GET.get('interval'):
            interval = request.GET['interval']

        if request.GET.get('year'):
            year = request.GET['year']

        if request.GET.get('variable'):
            variable = request.GET['variable']

        try:

            ts = get_point_stats(variable,float(lat),float(lon),interval,year)

            json_obj["time_series"] = ts
            json_obj["interval"] = interval
            json_obj["success"] = "success"
        except Exception as e:
            json_obj["error"] = "Error processing request: "+str(e)

    return JsonResponse(json_obj)

def geo_json_stats(request):

    json_obj = {}


    if request.is_ajax() and request.method == 'POST':
        info = request.POST
        suffix = None
        geom = None
        interval = None
        year = None

        suffix = info.get('variable')
        interval = info.get('interval')
        interval = interval.lower()
        year = info.get('year')
        geom = info.get('geom')

        try:

            ts = get_feature_stats(suffix, geom, interval, year)

            json_obj["time_series"] = ts
            json_obj["success"] = "success"
        except Exception as e:
            json_obj["error"] = "Error processing request: " + str(e)

    return JsonResponse(json_obj)

def get_poly_ts(request):

    json_obj = {}

    if request.method == 'GET':
        info = request.GET

        suffix = info.get('variable')
        interval = info.get('interval')
        interval = interval.lower()
        year = info.get('year')
        geom = info.get('geom')

        try:

            ts = get_polygon_stats(suffix, geom, interval, year)

            json_obj["time_series"] = ts
            json_obj["success"] = "success"
            json_obj["interval"] = interval
        except Exception as e:
            json_obj["error"] = "Error processing request: " + str(e)

    return JsonResponse(json_obj)

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
def get_poly_ts_post(request):

    json_obj = {}

    if request.method == 'POST':
        info = request.POST

        suffix = info.get('variable')
        interval = info.get('interval')
        interval = interval.lower()
        year = info.get('year')
        geom = info.get('geom')

        try:

            ts = get_polygon_stats(suffix, geom, interval, year)

            json_obj["time_series"] = ts
            json_obj["success"] = "success"
            json_obj["interval"] = interval
        except Exception as e:
            json_obj["error"] = "Error processing request: " + str(e)

    return JsonResponse(json_obj)







