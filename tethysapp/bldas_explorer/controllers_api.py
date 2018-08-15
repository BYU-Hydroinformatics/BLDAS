"""controllers_api.py
    Inspired from controller written from the StreamFlow Prediction Tool : Credit to the original authors
    Michael Suffront & Alan D. Snow, 2017
    Author : Rohit Khattar
    License: BSD 3-Clause
"""
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render_to_response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes

from .exceptions import InvalidData, exceptions_to_http_status
from .controllers import (get_forecast_stats, get_units_title)

import xarray
import pandas as pd
from csv import writer as csv_writer


@exceptions_to_http_status
def get_forecast_streamflow_csv(request):
    """
    Retrieve the forecasted streamflow as CSV
    """
    # retrieve statistics
    try:
        forecast_data, watershed_name, subbasin_name, river_id, units = \
            get_forecast_stats(request)

    except Exception as e:
        print str(e)


    # prepare to write response for CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = \
        'attachment; filename=forecasted_streamflow_{0}_{1}_{2}.csv' \
        .format(watershed_name,
                subbasin_name,
                river_id)

    writer = csv_writer(response)
    forecast_df = pd.DataFrame(forecast_data)
    column_names = (forecast_df.columns.values +
                    [' ({}3/s)'.format(get_units_title(units))]
                    ).tolist()

    writer.writerow(['datetime'] + column_names)

    for row_data in forecast_df.itertuples():
        writer.writerow(row_data)

    return response


@api_view(['GET'])
@authentication_classes((TokenAuthentication, SessionAuthentication,))
@exceptions_to_http_status
def get_forecast(request):
    """
    Controller that will retrieve the SALDAS data
    in CSV format
    """
    return_format = request.GET.get('return_format')

    if return_format == 'csv':
        return get_forecast_streamflow_csv(request)
    else:
        raise InvalidData('Only CSV format supported as of now. ')
