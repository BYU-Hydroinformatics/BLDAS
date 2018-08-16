import datetime,fnmatch
import time,calendar
import sys
import os, shutil
from ftplib import FTP
import numpy as np
from itertools import groupby
import tempfile, shutil,sys
import calendar
from netCDF4 import Dataset
import gdal
import osr
import ogr
import requests
from config import SALDAS_DIR,ROOT_DIR
import rasterio
import random
import ast
from rasterstats import zonal_stats
import geojson
import json
import math
from shapely.geometry import Point



def get_pt_ts(variable,point):
    coords = point.split(',')
    lat = round(float(coords[1]), 2)
    lon = round(float(coords[0]), 2)
    input_dir = SALDAS_DIR
    # print(variable)
    ts_plot = []

    for dir in sorted(os.listdir(input_dir)):
        cur_dir = os.path.join(input_dir,dir)
        for file in sorted(os.listdir(cur_dir)):
            if 'HIST' in file:
                file_ls = str(file.split('.')[0]).split('_')[2][:-4]
                dt = datetime.datetime.strptime(file_ls, '%Y%m%d')
                time_stamp = time.mktime(dt.timetuple()) * 1000
                in_loc = os.path.join(cur_dir, file)
                lis_fid = Dataset(in_loc, 'r')  # Reading the netcdf file
                lis_var = lis_fid.variables  # Get the netCDF variables
                lats = lis_var['lat'][:]
                lons = lis_var['lon'][:]

                abslat = np.abs(lats - lat)
                abslon = np.abs(lons - lon)

                c = np.maximum(abslon, abslat)

                x, y = np.where(c == np.min(c))
                if variable == 'SoilMoist_tavg':
                    val = lis_var[variable][0,x[0],y[0]]
                else:
                    val = lis_var[variable][x[0],y[0]]
                ts_plot.append([time_stamp, float(val)])
                # print(time_stamp,val)
                ts_plot.sort()

    return ts_plot

# get_pt_ts('Tair_f_tavg','91.1,20.7')

def get_variables_meta():
    db_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'public/data/var_info.txt')
    variable_list = []
    with open(db_file, mode='r') as f:
        f.readline()  # Skip first line

        lines = f.readlines()

    for line in lines:
        if line != '':
            line = line.strip()
            linevals = line.split('|')
            variable_id = linevals[0]
            display_name = linevals[1]
            units = linevals[2]
            gs_id = linevals[3]
            start = linevals[4]
            end = linevals[5]
            vmin = linevals[6]
            vmax = linevals[7]
            scale = calc_color_range(float(vmin),float(vmax))
            variable_list.append({
                'id': variable_id,
                'display_name': display_name,
                'units': units,
                'gs_id': gs_id,
                'start':start,
                'end':end,
                'min':vmin,
                'max':vmax,
                'scale':scale
            })

    return variable_list

def calc_color_range(min,max):

    interval = float(abs((max - min) / 20))

    if interval == 0:
        scale = [0] * 20
    else:
        scale = np.arange(min, max, interval).tolist()

    return scale

def get_feature_stats(suffix,geom_data,interval,year):
    json_obj = {}

    input_folder = os.path.join(ROOT_DIR,str(suffix)+'_'+str(interval))
    months = []

    if interval == 'mm' or interval == '3m':
        for month in range(1, 13):
            months.append(last_day_of_month(datetime.date(int(year), month, 1)))
    #if interval == '3m':
    #    months = months[2:]
    features = []

    for i,val in enumerate(geom_data):
        gl_data = ast.literal_eval(geom_data[i])
        features.append(gl_data)

    # print(features)
    geom_collection = geojson.FeatureCollection(features)
    min = []
    mean = []
    max = []
    median = []
    jj = 0
    for i,file in enumerate(sorted(os.listdir(input_folder))):
        pattern = str(year) + '*'
        if file.endswith('.tif') and fnmatch.fnmatch(file, pattern):
            if (suffix == 'temp'):
                stats = zonal_stats(geom_collection, os.path.join(input_folder, file), stats="mean median")
                statsmax = zonal_stats(geom_collection, os.path.join(ROOT_DIR + 'tempMax_' + interval, file), stats="max")
                statsmin = zonal_stats(geom_collection, os.path.join(ROOT_DIR + 'tempMin_' + interval, file), stats="min")
            else:
                stats = zonal_stats(geom_collection, os.path.join(input_folder, file),stats="min mean max median")
            # stats = zonal_stats(geom_collection, os.path.join(input_folder, file), stats="min mean max median")
            time_stamp = None
            # print('-------------------------------------------------------------------------------')
            # print (file)
            if interval == 'dd':
                year = file.split('.')[0][:4]
                dekad = file.split('.')[0][-2:]
                month = file.split('.')[0][4:6]
                idx = getIndexBasedOnDecad(int(dekad),int(month),int(year))
                cur_date = getDateBasedOnIndex(int(idx),int(year))
                # start_date = year + '01' + '01'
                # cur_date = datetime.datetime.strptime(start_date, '%Y%m%d') + datetime.timedelta(days=int(i * 10))
                time_stamp = (time.mktime(cur_date.timetuple()) * 1000)

            if interval == 'mm':
                time_stamp = (time.mktime(months[jj].timetuple()) * 1000)

            if interval == '3m':
                time_stamp = (time.mktime(months[jj].timetuple()) * 1000)
            if (suffix == 'temp'):
                min.append([time_stamp, statsmin[0]["min"]])
                max.append([time_stamp, statsmax[0]["max"]])
                median.append([time_stamp, stats[0]["median"]])
                mean.append([time_stamp, stats[0]["mean"]])
            else:
                min.append([time_stamp, stats[0]["min"]])
                max.append([time_stamp, stats[0]["max"]])
                median.append([time_stamp, stats[0]["median"]])
                mean.append([time_stamp, stats[0]["mean"]])
            # min.append([time_stamp,stats[0]["min"]])
            # max.append([time_stamp, stats[0]["max"]])
            # median.append([time_stamp, stats[0]["median"]])
            # mean.append([time_stamp, stats[0]["mean"]])
            jj = jj + 1
    #
    json_obj["min_data"] = sorted(min)
    json_obj["max_data"] = sorted(max)
    json_obj["median_data"] = sorted(median)
    json_obj["mean_data"] = sorted(mean)


    return json_obj

def get_polygon_stats(suffix,geom_data,interval,year):
    json_obj = {}
    input_folder = os.path.join(ROOT_DIR,str(suffix) + '_' + str(interval))
    months = []

    if interval == 'mm' or interval == '3m':
        for month in range(1, 13):
            months.append(last_day_of_month(datetime.date(int(year), month, 1)))

    # if interval == '3m':
    #     months = months[2:]

    min = []
    mean = []
    max = []
    median = []
    jj = 0

    for i, file in enumerate(sorted(os.listdir(input_folder))):
        pattern = str(year) + '*'
        if file.endswith('.tif') and fnmatch.fnmatch(file, pattern):
            if (suffix == 'temp'):
                stats = zonal_stats(geom_data, os.path.join(input_folder, file), stats="mean median")
                statsmax = zonal_stats(geom_data, os.path.join(ROOT_DIR + 'tempMax_' + interval, file), stats="max")
                statsmin = zonal_stats(geom_data, os.path.join(ROOT_DIR + 'tempMin_' + interval, file), stats="min")
            else:
                stats = zonal_stats(geom_data, os.path.join(input_folder, file),stats="min mean max median")
            # stats = zonal_stats(geom_data, os.path.join(input_folder,file), stats="min mean max median")
            time_stamp = None

            if interval == 'dd':
                year = file.split('.')[0][:4]
                dekad = file.split('.')[0][-2:]
                month = file.split('.')[0][4:6]
                idx = getIndexBasedOnDecad(int(dekad),int(month),int(year))
                cur_date = getDateBasedOnIndex(int(idx),int(year))
                # start_date = year + '01' + '01'
                # cur_date = datetime.datetime.strptime(start_date, '%Y%m%d') + datetime.timedelta(days=int(i * 10))
                time_stamp = (time.mktime(cur_date.timetuple()) * 1000)

            if interval == 'mm':
                time_stamp = (time.mktime(months[jj].timetuple()) * 1000)

            if interval == '3m':
                time_stamp = (time.mktime(months[jj].timetuple()) * 1000)
            if (suffix == 'temp'):
                min.append([time_stamp, statsmin[0]["min"]])
                max.append([time_stamp, statsmax[0]["max"]])
                median.append([time_stamp, stats[0]["median"]])
                mean.append([time_stamp, stats[0]["mean"]])
            else:
                min.append([time_stamp, stats[0]["min"]])
                max.append([time_stamp, stats[0]["max"]])
                median.append([time_stamp, stats[0]["median"]])
                mean.append([time_stamp, stats[0]["mean"]])
            # min.append([time_stamp, stats[0]["min"]])
            # max.append([time_stamp, stats[0]["max"]])
            # median.append([time_stamp, stats[0]["median"]])
            # mean.append([time_stamp, stats[0]["mean"]])
            jj = jj + 1

    json_obj["min_data"] = sorted(min)
    json_obj["max_data"] = sorted(max)
    json_obj["median_data"] = sorted(median)
    json_obj["mean_data"] = sorted(mean)

    return json_obj

# def get_polygon_statsRange(suffix,geom_data,interval,year, month, range):
#     # suffix = variable like temp, soilMoist, rain, evap
#     # interval = peroid like mm, dd, yy
#     # year = 2001
#     json_obj = {}
#
#     input_folder = os.path.join(ROOT_DIR,str(suffix) + '_' + str(interval))
#
#     months = []
#
#     if interval == 'mm' or interval == '3m':
#         for month in range(1, 13):
#             months.append(last_day_of_month(datetime.date(int(year), month, 1)))
#
#     # if interval == '3m':
#     #     months = months[2:]
#
#     min = []
#     mean = []
#     max = []
#     median = []
#
#     for i, file in enumerate(sorted(os.listdir(input_folder))):
#         if file.endswith('.tif'):
#             stats = zonal_stats(geom_data, os.path.join(input_folder,file),
#                         stats="min mean max median")
#             time_stamp = None
#
#             if interval == 'dd':
#                 year = file.split('.')[0][:4]
#                 dekad = file.split('.')[0][-2:]
#                 month = file.split('.')[0][4:6]
#                 idx = getIndexBasedOnDecad(int(dekad),int(month),int(year))
#                 cur_date = getDateBasedOnIndex(int(idx),int(year))
#                 # start_date = year + '01' + '01'
#                 # cur_date = datetime.datetime.strptime(start_date, '%Y%m%d') + datetime.timedelta(days=int(i * 10))
#                 time_stamp = (time.mktime(cur_date.timetuple()) * 1000)
#
#             if interval == 'mm':
#                 time_stamp = (time.mktime(months[i].timetuple()) * 1000)
#
#             if interval == '3m':
#                 time_stamp = (time.mktime(months[i].timetuple()) * 1000)
#
#             min.append([time_stamp, stats[0]["min"]])
#             max.append([time_stamp, stats[0]["max"]])
#             median.append([time_stamp, stats[0]["median"]])
#             mean.append([time_stamp, stats[0]["mean"]])
#
#     json_obj["min_data"] = sorted(min)
#     json_obj["max_data"] = sorted(max)
#     json_obj["median_data"] = sorted(median)
#     json_obj["mean_data"] = sorted(mean)
#
#     return json_obj

def get_polygon_statsRange(suffix,geom_data,interval,year, mon, rang):
    # suffix = variable like temp, soilMoist, rain, evap
    # interval = peroid like mm, dd, yy
    # year = 2001
    json_obj = {}
    if rang >= 12: # number of months to expand, max is 12
        rang = 12
    mon = int(mon)

    input_folder = os.path.join(ROOT_DIR,str(suffix) + '_' + str(interval))
    months = []

    if interval == 'mm' or interval == '3m':
        # for pp in range(1, 13):
        for pp in range(mon, mon + rang):
            if pp > 12: #if mooth is 12 then go to next year
                mn = pp - 12
                curYr = year + 1
            else:
                mn = pp
                curYr = year
            months.append(last_day_of_month(datetime.date(int(curYr), mn, 1)))

    # if interval == '3m':
    #     months = months[2:]

    min = []
    mean = []
    max = []
    median = []
    jj = 0
    for i, file in enumerate(sorted(os.listdir(input_folder))):
        pattern = ''
        for pp in range(mon, mon + rang):
            if pp > 12: #if mooth is 12 then go to next year
                mn = pp - 12
                curYr = int(year) + 1
            else:
                mn = pp
                curYr = year
            pattern = str(curYr) + str(format(mn,'02d') + '*')
            if file.endswith('.tif') and fnmatch.fnmatch(file, pattern):
                if (suffix == 'temp'):
                    stats = zonal_stats(geom_data, os.path.join(input_folder, file), stats="mean median")
                    statsmax = zonal_stats(geom_data, os.path.join(ROOT_DIR + 'tempMax_' + interval, file), stats="max")
                    statsmin = zonal_stats(geom_data, os.path.join(ROOT_DIR + 'tempMin_' + interval, file), stats="min")
                else:
                    stats = zonal_stats(geom_data, os.path.join(input_folder, file), stats="min mean max median")
                # stats = zonal_stats(geom_data, os.path.join(input_folder,file),stats="min mean max median")
                time_stamp = None

                if interval == 'dd':
                    yearDD = file.split('.')[0][:4]
                    dekad = file.split('.')[0][-2:]
                    month = file.split('.')[0][4:6]
                    idx = getIndexBasedOnDecad(int(dekad),int(month),int(yearDD))
                    cur_date = getDateBasedOnIndex(int(idx),int(yearDD))
                    # start_date = year + '01' + '01'
                    # cur_date = datetime.datetime.strptime(start_date, '%Y%m%d') + datetime.timedelta(days=int(i * 10))
                    time_stamp = (time.mktime(cur_date.timetuple()) * 1000)

                if interval == 'mm':
                    time_stamp = (time.mktime(months[jj].timetuple()) * 1000)

                if interval == '3m':
                    time_stamp = (time.mktime(months[jj].timetuple()) * 1000)

                if (suffix == 'temp'):
                    min.append([time_stamp, statsmin[0]["min"]])
                    max.append([time_stamp, statsmax[0]["max"]])
                    median.append([time_stamp, stats[0]["median"]])
                    mean.append([time_stamp, stats[0]["mean"]])
                else:
                    min.append([time_stamp, stats[0]["min"]])
                    max.append([time_stamp, stats[0]["max"]])
                    median.append([time_stamp, stats[0]["median"]])
                    mean.append([time_stamp, stats[0]["mean"]])

                # min.append([time_stamp, stats[0]["min"]])
                # max.append([time_stamp, stats[0]["max"]])
                # median.append([time_stamp, stats[0]["median"]])
                # mean.append([time_stamp, stats[0]["mean"]])
                jj = jj + 1
                break

    json_obj["min_data"] = sorted(min)
    json_obj["max_data"] = sorted(max)
    json_obj["median_data"] = sorted(median)
    json_obj["mean_data"] = sorted(mean)

    return json_obj

def get_point_stats(suffix,lat,lon,interval,year):
    json_obj = {}
    interval = interval.lower()
    point = Point(lon,lat)

    input_folder = os.path.join(ROOT_DIR, str(suffix) + '_' + str(interval))
    months = []

    if interval == 'mm' or interval == '3m':
        for month in range(1, 13):
            months.append(last_day_of_month(datetime.date(int(year), month, 1)))
        # print (months)
    # if interval == '3m':
    #     months = months[2:]

    min = []
    mean = []
    max = []
    median = []
    jj = 0
    for i, file in enumerate(sorted(os.listdir(input_folder))):
        pattern = str(year) + '*'
        if file.endswith('.tif') and fnmatch.fnmatch(file, pattern):
            if (suffix == 'temp'):
                stats = zonal_stats(point, os.path.join(input_folder, file), stats="mean median")
                statsmax = zonal_stats(point, os.path.join(ROOT_DIR + 'tempMax_' + interval, file), stats="max")
                statsmin = zonal_stats(point, os.path.join(ROOT_DIR + 'tempMin_' + interval, file), stats="min")
            else:
                stats = zonal_stats(point, os.path.join(input_folder, file),stats="min mean max median")
            time_stamp = None
            if interval == 'dd':
                year = file.split('.')[0][:4]
                dekad = file.split('.')[0][-2:]
                month = file.split('.')[0][4:6]
                idx = getIndexBasedOnDecad(int(dekad),int(month),int(year))
                cur_date = getDateBasedOnIndex(int(idx),int(year))
                # start_date = year + '01' + '01'
                # cur_date = datetime.datetime.strptime(start_date, '%Y%m%d') + datetime.timedelta(days=int(i * 10))
                time_stamp = (time.mktime(cur_date.timetuple()) * 1000)

            if interval == 'mm':
                time_stamp = (time.mktime(months[jj].timetuple()) * 1000)

            if interval == '3m':
                time_stamp = (time.mktime(months[jj].timetuple()) * 1000)
            if (suffix == 'temp'):
                min.append([time_stamp, statsmin[0]["min"]])
                max.append([time_stamp, statsmax[0]["max"]])
                median.append([time_stamp, stats[0]["median"]])
                mean.append([time_stamp, stats[0]["mean"]])
            else:
                min.append([time_stamp, stats[0]["min"]])
                max.append([time_stamp, stats[0]["max"]])
                median.append([time_stamp, stats[0]["median"]])
                mean.append([time_stamp, stats[0]["mean"]])
            jj = jj +1

    json_obj["min_data"] = sorted(min)
    json_obj["max_data"] = sorted(max)
    json_obj["median_data"] = sorted(median)
    json_obj["mean_data"] = sorted(mean)

    return json_obj

def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)

def convertEpochToJulianDay(epochTime):
    return int(time.strftime("%j",time.gmtime(epochTime)))

def convertDayMonthYearToEpoch(day,month,year):
    return float(datetime.date(year, month, day).strftime("%s"))

def getLastDayOfMonth(month,year):
    monthToProcess = month+1
    yearToProcess = year
    if (month == 12):
        monthToProcess = 1
        yearToProcess = year+1
    epochTime = float(datetime.date(yearToProcess, monthToProcess, 1).strftime("%s"))-86400
    return int(time.strftime("%d",time.gmtime(epochTime)))

def getIndexesBasedOnEpoch(startEpochTime, endEpochTime):
        jStart = convertEpochToJulianDay(startEpochTime)
        jEnd = convertEpochToJulianDay(endEpochTime)
        start = int(jStart / 10.)
        end = int(math.ceil((jEnd) / 10.))
        if (start == end):
            return [start]
        return range(start, end)

def getIndexBasedOnEpoch(startEpochTime):
        return int(convertEpochToJulianDay(startEpochTime) / 10.)

def getIndexBasedOnDate(day, month, year):
    decad = None
    if int(day) <= int(10):
        decad = int(1)
    elif int(day) <= int(20) and int(day) > int(10) and int(month) != int(2):
        decad = int(2)
    elif int(day) <= int(31) and int(day) > int(20) and int(month) != int(2):
        decad = int(3)
    elif int(day) <= int(20) and int(day) > int(10) and int(month) == int(2):
        decad = int(2)
    elif int(day) <= int(29) and int(day) > int(20) and int(month) == int(2):
        decad = int(3)

    return getIndexBasedOnDecad(decad, month, year)

def getIndexBasedOnDecad(decad, month, year):
    tIn = [x for x in range(0, 36)]
    decadChunks = [tIn[i:i + 3] for i in range(0, len(tIn), 3)]

    return int(decadChunks[int(month) - 1][int(decad) - 1])

def getDateBasedOnIndex(index, year):
    tIn = [x for x in range(0, 36)]
    decadChunks = [tIn[i:i + 3] for i in range(0, len(tIn), 3)]
    decadIndex = [[i, j] for i, lst in enumerate(decadChunks) for j, pos in enumerate(lst) if pos == index]
    month = int((decadIndex)[0][0]) + 1
    decad = int((decadIndex)[0][1]) + 1
    if int(decad) != int(3):
        return datetime.datetime(year, month, 10) + datetime.timedelta(decadIndex[0][1] * 10.)
    else:
        any_day = datetime.datetime(year, month, 10)
        next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
        return next_month - datetime.timedelta(days=next_month.day)

def indexAndYearToDate(year, index):
    return datetime.date(year, 1, 1) + datetime.timedelta(days=index * 10.)

def getIndexesBasedOnDate(daystart, monthstart, yearstart, dayend, monthend, yearend):
    return getIndexesBasedOnEpoch(convertDayMonthYearToEpoch(daystart, monthstart, yearstart),
                                       convertDayMonthYearToEpoch(dayend, monthend, yearend))

# Nishanta code start
from rasterio.mask import mask

def get_polygon_areaRange(suffix,geom_data,interval,year, mon, rang, minVal, maxVal):
    # create arrays to store the size  of pixel of variables
    pixel_size = {};
    pixel_size[25] = ['emodisNdvi','temp','evap','soilMoist','NDVI','ndviAnomaly','rain','ch2Spi']

    # suffix = variable like temp, soilMoist, rain, evap
    # interval = peroid like mm, dd, yy
    # year = 2001
    json_obj = {}
    if rang >= 12: # number of months to expand, max is 12
        rang = 12
    mon = int(mon)

    input_folder = os.path.join(ROOT_DIR,str(suffix) + '_' + str(interval))
    months = []

    if interval == 'mm' or interval == '3m':
        # for pp in range(1, 13):
        for pp in range(mon, mon + rang):
            if pp > 12: #if mooth is 12 then go to next year
                mn = pp - 12
                curYr = year + 1
            else:
                mn = pp
                curYr = year
            months.append(last_day_of_month(datetime.date(int(curYr), mn, 1)))

    # if interval == '3m':
    #     months = months[2:]
    area_under = []
    jj = 0

    # go through all existing files
    for i, file in enumerate(sorted(os.listdir(input_folder))):
        pattern = ''
        for pp in range(mon, mon + rang):
            if pp > 12: #if mooth is 12 then go to next year
                mn = pp - 12
                curYr = int(year) + 1
            else:
                mn = pp
                curYr = year
            pattern = str(curYr) + str(format(mn,'02d') + '*')
            # check if current file is one of the required files
            if file.endswith('.tif') and fnmatch.fnmatch(file, pattern):
                #parse geometry to an object
                try:
                    geom_json = [json.loads(geom_data)]
                except:
                    with fiona.open(geom_data, "r") as shapefile:
                        geom_json = [feature["geometry"] for feature in shapefile]
                #open the required tif file
                with rasterio.open(os.path.join(input_folder,file)) as src:
                    #apply geom mask and crop the image
                    masked_image, masked_transform = mask(src, geom_json, crop=True)
                #create a temporary copy of masked image
                temp_mask_image = masked_image
                #get nodata value of source image
                nodata = src.nodata
                #get all the pixels and set set masked values as false
                temp_mask_image = masked_image != nodata
                if (minVal != None):
                    #combine the previous result with minimum threshold
                    temp_mask_image = np.logical_and(temp_mask_image, masked_image > minVal)
                if (maxVal != None):
                    #combine previous results with the maximum threshold
                    temp_mask_image = np.logical_and(temp_mask_image, masked_image <= maxVal)

                #count the number of true values to get number of valid pixels
                num_of_pixels = np.sum(temp_mask_image)

                total_area = 0
                pixel_area = 0
                #multiply the number of pixels by the area per pixel (length of pixel ^ 2)
                if (suffix in pixel_size[25]):
                    pixel_area = 25
                    total_area = num_of_pixels * pixel_area

                # compute timestamp for the current image
                time_stamp = None

                if interval == 'dd':
                    yearDD = file.split('.')[0][:4]
                    dekad = file.split('.')[0][-2:]
                    month = file.split('.')[0][4:6]
                    idx = getIndexBasedOnDecad(int(dekad),int(month),int(yearDD))
                    cur_date = getDateBasedOnIndex(int(idx),int(yearDD))
                    # start_date = year + '01' + '01'
                    # cur_date = datetime.datetime.strptime(start_date, '%Y%m%d') + datetime.timedelta(days=int(i * 10))
                    time_stamp = (time.mktime(cur_date.timetuple()) * 1000)

                if interval == 'mm':
                    time_stamp = (time.mktime(months[jj].timetuple()) * 1000)

                if interval == '3m':
                    time_stamp = (time.mktime(months[jj].timetuple()) * 1000)

                area_under.append([time_stamp, total_area])
                jj = jj + 1
                break

    json_obj["area_under"] = area_under
    json_obj["pixel_area"] = pixel_area
    return json_obj

# Nishanta code end



