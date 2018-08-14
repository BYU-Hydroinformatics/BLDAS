from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from utils import *
from django.http import JsonResponse
from config import *

def home(request):
    """
    Controller for the app home page.
    """
    dekad_options = []
    month_options = []
    quarter_options = []

    for i in range(1,13):
        for j in range(1,4):
            dekad = format(j, "02d")
            month = format(i, "02d")
            option = [str(month)+str(dekad),'Dekad '+datetime.date(2017, i, 1).strftime('%B') +' '+str(dekad)]
            dekad_options.append(option)

    for i in range(1, 13):
        month_options.append([datetime.date(2017, i, 1).strftime('%m'), datetime.date(2017, i, 1).strftime('%B')])

    for i in range(len(month_options) - 2):
        quarter = str(format(i + 1, '02d')) + str(format(i + 2, '02d')) + str(format(i + 3, '02d'))
        quarter_options.append([quarter,'Quarter '+str(quarter)])

    variable_info = get_variables_meta()
    geoserver_wms_url = geoserver["wms_url"]
    # print (dekad_options)

    context = {
        'variable_info': json.dumps(variable_info),
        'dekad_options':json.dumps(dekad_options),
        'month_options':json.dumps(month_options),
        'quarter_options':json.dumps(quarter_options),
        'geoserver_wms_url': geoserver_wms_url,
    }

    return render(request, 'bldas_explorer/home.html', context)

def get_plot(request):
    return_obj = {}

    if request.is_ajax() and request.method == 'POST':
        info = request.POST

        variable = info.get("variable")
        interaction = info.get('interaction')
        interval = info.get('interval')
        interval = interval.lower()
        year = info.get('year')
        return_obj["variable"] = variable

        var_list = get_variables_meta()
        var_idx = next((index for (index, d) in enumerate(var_list) if d["id"] == variable), None)

        suffix = (var_list[var_idx]["gs_id"])

        # point = request.POST['point']
        # polygon = request.POST['polygon']
        if interaction == 'District':
            geom_data = request.POST.getlist("geom_data[]")

            ts = get_feature_stats(suffix,geom_data,interval,year)
            return_obj["time_series"] = ts
            return_obj["success"] = "success"
            return_obj["interaction"] = "district"

        if interaction == 'Point':
            try:
                geom_data = request.POST["geom_data"]
                coords = geom_data.split(',')
                lat = round(float(coords[1]), 2)
                lon = round(float(coords[0]), 2)
                # print(geom_data)
                # ts = get_pt_ts(variable,geom_data)
                ts = get_point_stats(suffix,lat,lon,interval,year)
                return_obj["time_series"] = ts
                return_obj["interaction"] = "point"
                return_obj["success"] = "success"
            except Exception as e:
                return_obj["error"] = "Error Processing Request: "+ str(e)

        if interaction == 'Polygon':
            geom_data = request.POST["geom_data"]

            try:
                ts = get_polygon_stats(suffix,geom_data,interval,year)
                return_obj["time_series"] = ts
                return_obj["interaction"] = "polygon"
                return_obj["success"] = "success"
            except Exception as e:
                return_obj["error"] = "Error processing request: " + str(e)

    return JsonResponse(return_obj)
