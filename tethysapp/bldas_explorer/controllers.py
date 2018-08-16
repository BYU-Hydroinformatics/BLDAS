from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from utils import *
from django.http import JsonResponse
from config import *

import plotly.graph_objs as go
import netCDF4 as nc
import datetime as dt
import numpy as np

import xarray

from .exceptions import (SettingsError,
                         exceptions_to_http_status,
                         rivid_exception_handler)


def home(request):
    dekad_options = []
    month_options = []
    quarter_options = []

    for i in range(1, 13):
        for j in range(1, 4):
            dekad = format(j, "02d")
            month = format(i, "02d")
            option = [str(month)+str(dekad), 'Dekad ' +
                      datetime.date(2017, i, 1).strftime('%B') + ' '+str(dekad)]
            dekad_options.append(option)

    for i in range(1, 13):
        month_options.append([datetime.date(2017, i, 1).strftime(
            '%m'), datetime.date(2017, i, 1).strftime('%B')])

    for i in range(len(month_options) - 2):
        quarter = str(format(i + 1, '02d')) + \
            str(format(i + 2, '02d')) + str(format(i + 3, '02d'))
        quarter_options.append([quarter, 'Quarter '+str(quarter)])

    variable_info = get_variables_meta()
    geoserver_wms_url = geoserver["wms_url"]

    context = {
        'variable_info': json.dumps(variable_info),
        'dekad_options': json.dumps(dekad_options),
        'month_options': json.dumps(month_options),
        'quarter_options': json.dumps(quarter_options),
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
        var_idx = next((index for (index, d) in enumerate(
            var_list) if d["id"] == variable), None)

        suffix = (var_list[var_idx]["gs_id"])

        # point = request.POST['point']
        # polygon = request.POST['polygon']
        if interaction == 'District':
            geom_data = request.POST.getlist("geom_data[]")

            ts = get_feature_stats(suffix, geom_data, interval, year)
            return_obj["time_series"] = ts
            return_obj["success"] = "success"
            return_obj["interaction"] = "district"

        if interaction == 'Point':
            try:
                geom_data = request.POST["geom_data"]
                coords = geom_data.split(',')
                lat = round(float(coords[1]), 2)
                lon = round(float(coords[0]), 2)
                # ts = get_pt_ts(variable,geom_data)
                ts = get_point_stats(suffix, lat, lon, interval, year)
                return_obj["time_series"] = ts
                return_obj["interaction"] = "point"
                return_obj["success"] = "success"
            except Exception as e:
                return_obj["error"] = "Error Processing Request: " + str(e)

        if interaction == 'Polygon':
            geom_data = request.POST["geom_data"]

            try:
                ts = get_polygon_stats(suffix, geom_data, interval, year)
                return_obj["time_series"] = ts
                return_obj["interaction"] = "polygon"
                return_obj["success"] = "success"
            except Exception as e:
                return_obj["error"] = "Error processing request: " + str(e)

    return JsonResponse(return_obj)


def get_chart_from_nc(ncFilePath, comid, units):
    res = nc.Dataset(ncFilePath, 'r')

    dates_raw = res.variables['time'][:]

    dates = []
    for d in dates_raw:
        dates.append(dt.datetime.fromtimestamp(d))

    comid_list = res.variables['rivid'][:]

    try:
        comid_index = int(np.where(comid_list == int(comid))[0])
    except Exception as e:
        raise ValueError(
            'No matching COMID found for the feature in our dataset. Please check the dataset or the feature layer')

    values = []
    for l in list(res.variables['Qout'][:]):
        values.append(float(l[comid_index]))

    # --------------------------------------
    # Chart Section
    # --------------------------------------
    series = go.Scatter(
        name='LDAS',
        x=dates,
        y=values,
        )

    layout = go.Layout(
        title="LDAS Streamflow <br><sub>Nepal (South Asia): {0}</sub>".format(
            comid),
        xaxis=dict(
            title='Date',
            ),
        yaxis=dict(
            title='Streamflow ({}<sup>3</sup>/s)'.format(get_units_title(units))
            ),
        width='100%',
        height='100%',
        margin=go.Margin(
            l=80,
            r=50,
            b=50,
            t=100,
            pad=4
            )
        )

    chart_obj = PlotlyView(
        go.Figure(data=[series],
                  layout=layout)
        )

    return chart_obj

# returns both historical and forecast data


def get_lis(request):
    get_data = request.GET

    try:
        comid = get_data.get('comid')
        units = 'metric'

        if(get_data.get('type') == 'historical'):

            filename = [f for f in os.listdir(LIS_DIR) if 'Qout' in f]
            filePath = os.path.join(LIS_DIR, filename[0])
            try:
                historical_chart = get_chart_from_nc(filePath, comid, units)
                context = {'chart': historical_chart}

                return render(request, 'bldas_explorer/charts.html', context)

            except ValueError as err:
                print str(err)
                return JsonResponse({'Error': str(err)})

        elif (get_data.get('type') == 'forecast'):
            filename = [f for f in os.listdir(FOREACAST_DIR) if 'Qout' in f]
            filePath = os.path.join(FOREACAST_DIR, filename[0])

            if filename:
                try:
                    forecast_chart = get_chart_from_nc(filePath, comid, units)
                    context = {'chart': forecast_chart}

                    return render(request, 'bldas_explorer/charts.html', context)

                except ValueError as err:
                    print str(err)
                    return JsonResponse({'Error': str(err)})
            else:
                return JsonResponse({'error': 'No files found for this type of data'})

        else:
            return JsonResponse({'error': 'Please specify type of data. historical or forecast'})

    except Exception as e:
        print str(e)
        return JsonResponse({'error': 'No LIS data found for the selected reach.'})


def get_units_title(unit_type):
    units_title = "m"
    if unit_type == 'english':
        units_title = "ft"
    return units_title


@exceptions_to_http_status
def get_forecast_stats(request):
    """
    Returns the forecast for the requested river
    """
    path_to_rapid_output = os.path.join(LIS_DIR)

    if not os.path.exists(path_to_rapid_output):
        raise SettingsError('Location of forecast files faulty. '
                            'Please check Config Files.')

    # get information from AJAX request
    get_info = request.GET
    watershed_name = get_info.get('watershed_name')
    subbasin_name = get_info.get('subbasin_name')
    river_id = get_info.get('river_id')
    units = get_info.get('units')
    dType = get_info.get('type')

    # Get the dataset. In our current situtation there aren't a lot of datasets but just one.
    # this might change in the future so we would need to add some additional logic here to handle that
    return_dict = {}

    if(dType == 'historical'):

        filename = [f for f in os.listdir(LIS_DIR) if 'Qout' in f]
        filePath = os.path.join(LIS_DIR, filename[0])

    elif (dType == 'forecast'):
        filename = [f for f in os.listdir(FOREACAST_DIR) if 'Qout' in f]
        filePath = os.path.join(FOREACAST_DIR, filename[0])

    else:
        raise ValueError(
            'Invalid Type of data. Only forecast or historical supported')
        return

    merged_ds = xarray.open_dataset(filePath, autoclose=True).sel(
        rivid=long(river_id)).Qout

    return_dict['mean'] = merged_ds.to_dataframe().Qout

    return return_dict, watershed_name, subbasin_name, river_id, units
