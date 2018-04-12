from datetime import datetime
import datetime
import time
import sys
import os, shutil
from ftplib import FTP
import numpy as np
from itertools import groupby
import tempfile, shutil,sys
import calendar
from utils import *
from netCDF4 import Dataset
import gdal
import osr
import ogr
import requests
from config import SALDAS_DIR
import rasterio
import random
from collections import defaultdict

def aggregateRastersQuarterly(input_dir,output_dir,operation):
    output_dir = os.path.join(output_dir, "")
    l = sorted(os.listdir(input_dir))
    inDs = gdal.Open(os.path.join(input_dir, l[0]))

    ysize = inDs.RasterYSize
    xsize = inDs.RasterXSize
    GeoT = inDs.GetGeoTransform()
    Projection = inDs.GetProjection()
    NDV = inDs.GetRasterBand(1).GetNoDataValue()

    for i in range(len(l)-2):
        array_list = [read_file(os.path.join(input_dir,x)) for x in l[i:i+3]]
        year = l[i].split('.')[0][:4]
        array_out = None
        if operation == 'average':
            array_out = np.mean(array_list, axis=0)
        if operation == 'sum':
            array_out = np.sum(array_list, axis=0)
        quarter = str(format(i + 1,'02d'))+str(format(i + 2,'02d'))+str(format(i + 3,'02d'))
        file_name = year + str(quarter) + '.tif'
        print(file_name)
        driver = gdal.GetDriverByName('GTiff')
        DataSet = driver.Create(output_dir + str(file_name), xsize, ysize, 1, gdal.GDT_Float32)
        DataSet.SetGeoTransform(GeoT)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        DataSet.SetProjection(srs.ExportToWkt())

        DataSet.GetRasterBand(1).WriteArray(array_out)
        DataSet.GetRasterBand(1).SetNoDataValue(NDV)
        DataSet.FlushCache()

        DataSet = None

def aggregateRastersDekad(input_dir,output_dir,operation):
    output_dir = os.path.join(output_dir, "")
    l = sorted(os.listdir(input_dir))

    d = defaultdict(list)
    for file in l:
        dt_str = file.split('.')[0]
        day = dt_str[-2:]
        month = dt_str[4:6]
        year = dt_str[:4]
        idx = getIndexBasedOnDate(day,month,year)
        d[idx].append(file)

    inDs = gdal.Open(os.path.join(input_dir, l[0]))

    ysize = inDs.RasterYSize
    xsize = inDs.RasterXSize
    GeoT = inDs.GetGeoTransform()
    Projection = inDs.GetProjection()
    NDV = inDs.GetRasterBand(1).GetNoDataValue()

    for step,key in enumerate(d):

        month = d[key][0].split('.')[0][4:6]
        dd_val = d[key][0].split('.')[0][-2:]
        year = d[key][0].split('.')[0][:4]
        if dd_val == '01':
            dekad = '01'
        elif dd_val == '11':
            dekad = '02'
        elif dd_val == '21':
            dekad = '03'

        array_list = [read_file(os.path.join(input_dir,x)) for x in d[key]]

        array_out = None
        if operation == 'average':
            array_out = np.mean(array_list, axis=0)
        if operation == 'sum':
            array_out = np.sum(array_list, axis=0)

        file_name = year + str(month)+str(dekad) + '.tif'
        print(file_name)
        driver = gdal.GetDriverByName('GTiff')
        DataSet = driver.Create(output_dir + str(file_name), xsize, ysize, 1, gdal.GDT_Float32)
        DataSet.SetGeoTransform(GeoT)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        DataSet.SetProjection(srs.ExportToWkt())

        DataSet.GetRasterBand(1).WriteArray(array_out)
        DataSet.GetRasterBand(1).SetNoDataValue(NDV)
        DataSet.FlushCache()

        DataSet = None

def aggregateRastersMonthly(input_dir,output_dir,operation):
    output_dir = os.path.join(output_dir, "")
    l = sorted(os.listdir(input_dir))
    grouped = [list(g) for k, g in groupby(l, lambda x: x[4:6])]

    inDs = gdal.Open(os.path.join(input_dir, l[0]))

    ysize = inDs.RasterYSize
    xsize = inDs.RasterXSize
    GeoT = inDs.GetGeoTransform()
    Projection = inDs.GetProjection()
    NDV = inDs.GetRasterBand(1).GetNoDataValue()
    # print(NDV)
    for step,chunk in enumerate(grouped):
        # array_list = [read_file(os.path.join(input_dir,x) for x in chunk]
        year = chunk[0].split('.')[0][:4]
        array_list = [read_file(os.path.join(input_dir,x)) for x in chunk]

        array_out = None
        if operation == 'average':
            array_out = np.mean(array_list, axis=0)
        if operation == 'sum':
            array_out = np.sum(array_list, axis=0)
        month = format(step + 1,'02d')

        file_name = year + str(month) + '.tif'
        print(file_name)
        driver = gdal.GetDriverByName('GTiff')
        DataSet = driver.Create(output_dir + str(file_name), xsize, ysize, 1, gdal.GDT_Float32)
        DataSet.SetGeoTransform(GeoT)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        DataSet.SetProjection(srs.ExportToWkt())

        DataSet.GetRasterBand(1).WriteArray(array_out)
        DataSet.GetRasterBand(1).SetNoDataValue(NDV)
        DataSet.FlushCache()

        DataSet = None

def extractRasters(input_dir,output_dir,nc_var):
    for dir in sorted(os.listdir(input_dir)):
        cur_dir = os.path.join(input_dir,dir)
        for file in sorted(os.listdir(cur_dir)):
            if 'HIST' in file:
                in_loc = os.path.join(cur_dir, file)
                output_dir = os.path.join(output_dir, "")
                lis_fid = Dataset(in_loc, 'r')  # Reading the netcdf file
                lis_var = lis_fid.variables  # Get the netCDF variables
                xsize, ysize, GeoT, Projection, NDV = get_netcdf_info(in_loc, nc_var)
                # print(xsize,ysize,GeoT)
                date_str = file.split('_')[2][:8]
                data = lis_var[nc_var][:, :]
                data = data[::-1, :]
                lat = lis_var['lat'][:]
                lon = lis_var['lon'][:]
                xmin, ymin, xmax, ymax = [lon.min(), lat.min(), lon.max(), lat.max()]
                nrows, ncols = np.shape(data)
                xres = (xmax - xmin) / float(ncols)
                yres = (ymax - ymin) / float(nrows)
                geotransform = (xmin, xres, 0, ymax, 0, -yres)
                print(geotransform,GeoT)
                # print(lat,lon)
                driver = gdal.GetDriverByName('GTiff')
                print(output_dir + str(date_str) + '.tif')
                DataSet = driver.Create(output_dir + str(date_str) + '.tif', ncols, nrows, 1, gdal.GDT_Float32)
                DataSet.SetGeoTransform(geotransform)
                srs = osr.SpatialReference()
                srs.ImportFromEPSG(4326)
                DataSet.SetProjection(srs.ExportToWkt())

                DataSet.GetRasterBand(1).WriteArray(data)
                DataSet.GetRasterBand(1).SetNoDataValue(NDV)
                DataSet.FlushCache()

                DataSet = None

def extractSoilRasters(input_dir,output_dir,nc_var,profile):
    for dir in sorted(os.listdir(input_dir)):
        cur_dir = os.path.join(input_dir,dir)
        for file in sorted(os.listdir(cur_dir)):
            if 'HIST' in file:
                in_loc = os.path.join(cur_dir, file)
                output_dir = os.path.join(output_dir, "")
                lis_fid = Dataset(in_loc, 'r')  # Reading the netcdf file
                lis_var = lis_fid.variables  # Get the netCDF variables
                xsize, ysize, GeoT, Projection, NDV = get_netcdf_info(in_loc, nc_var)
                date_str = file.split('_')[2][:8]
                data = lis_var[nc_var][profile, :, :]
                data = data[::-1, :]
                lat = lis_var['lat'][:]
                lon = lis_var['lon'][:]
                xmin, ymin, xmax, ymax = [lon.min(), lat.min(), lon.max(), lat.max()]
                nrows, ncols = np.shape(data)
                xres = (xmax - xmin) / float(ncols)
                yres = (ymax - ymin) / float(nrows)
                geotransform = (xmin, xres, 0, ymax, 0, -yres)
                print(geotransform, GeoT)
                # print(lat,lon)
                driver = gdal.GetDriverByName('GTiff')
                print(output_dir + str(date_str) + '.tif')
                DataSet = driver.Create(output_dir + str(date_str) + '.tif', ncols, nrows, 1, gdal.GDT_Float32)
                DataSet.SetGeoTransform(geotransform)
                srs = osr.SpatialReference()
                srs.ImportFromEPSG(4326)
                DataSet.SetProjection(srs.ExportToWkt())

                DataSet.GetRasterBand(1).WriteArray(data)
                DataSet.GetRasterBand(1).SetNoDataValue(NDV)
                DataSet.FlushCache()

                DataSet = None

def read_file(file):
    with rasterio.open(file) as src:
        return(src.read(1))

#Get info from the netCDF file. This info will be used to convert the shapefile to a raster layer
def get_netcdf_info(filename,var_name):

    nc_file = gdal.Open(filename)

    if nc_file is None:
        sys.exit()

    #There are more than two variables, so specifying the lwe_thickness variable

    if nc_file.GetSubDatasets() > 1:
        subdataset = 'NETCDF:"'+filename+'":'+var_name #Specifying the subset name
        src_ds_sd = gdal.Open(subdataset) #Reading the subset
        NDV = src_ds_sd.GetRasterBand(1).GetNoDataValue() #Get the nodatavalues
        xsize = src_ds_sd.RasterXSize #Get the X size
        ysize = src_ds_sd.RasterYSize #Get the Y size
        GeoT = src_ds_sd.GetGeoTransform() #Get the GeoTransform
        Projection = osr.SpatialReference() #Get the SpatialReference
        Projection.ImportFromWkt(src_ds_sd.GetProjectionRef()) #Setting the Spatial Reference
        src_ds_sd = None #Closing the file
        nc_file = None #Closing the file

        return xsize,ysize,GeoT,Projection,NDV #Return data that will be used to convert the shapefile

def upload_tiff(dir,geoserver_rest_url,workspace,uname,pwd,variable):

    headers = {
        'Content-type': 'image/tiff',
    }

    for file in os.listdir(dir): #Looping through all the files in the given directory
        if file is None:
            print ("No files. Please check directory and try again.")
            sys.exit()
        if file.endswith('.tif'):
            data = open(os.path.join(dir,file),'rb').read() #Read the file
            store_name = variable + '_' +str(file.split('.')[0]) #Creating the store name dynamically
            print(store_name)
            request_url = '{0}workspaces/{1}/coveragestores/{2}/file.geotiff'.format(geoserver_rest_url,workspace,store_name) #Creating the rest url
            # print(request_url)
            requests.put(request_url,verify=False,headers=headers,data=data,auth=(uname,pwd)) #Creating the resource on the geoserver

# upload_tiff('/media/sf_Downloads/SALDAS_ROOT/temp_dd','http://192.168.10.75:8181/geoserver/rest/','saldasDD','Saldas','Sa1das##123','temp')
# upload_tiff('/media/sf_Downloads/SALDAS_ROOT/temp_mm','http://192.168.10.75:8181/geoserver/rest/','saldasMM','Saldas','Sa1das##123','temp')
# upload_tiff('/media/sf_Downloads/SALDAS_ROOT/temp_3m','http://192.168.10.75:8181/geoserver/rest/','saldas3M','Saldas','Sa1das##123','temp')
#aggregateRastersQuarterly('/media/sf_Downloads/SALDAS_TemperatureMonthly/','/media/sf_Downloads/SALDAS_TemperatureQuarterly/')
#aggregateRastersMonthly('/media/sf_Downloads/SALDAS_Temperature/','/media/sf_Downloads/SALDAS_TemperatureMonthly/')
#aggregateRastersDekad('/media/sf_Downloads/SALDAS_Temperature/','/media/sf_Downloads/SALDAS_TemperatureDekad/')
#aggregateRasterQuarterly('/media/sf_Downloads/SALDAS_Temperature/','/media/sf_Downloads/SALDAS_TemperatureDekad/')
#extractRasters(SALDAS_DIR,'/media/sf_Downloads/SALDAS_Evap/','Evap_tavg')
#aggregateRastersDekad('/media/sf_Downloads/SALDAS_Temperature/','/media/sf_Downloads/SALDAS_temp_dd/','average')
#aggregateRastersQuarterly('/media/sf_Downloads/SALDAS_rain_mm/','/media/sf_Downloads/SALDAS_rain_3m/','sum')
#aggregateRastersQuarterly('/media/sf_Downloads/SALDAS_soilMoist_mm/','/media/sf_Downloads/SALDAS_soilMoist_3m/','average')
#aggregateRastersQuarterly('/media/sf_Downloads/SALDAS_temp_mm/','/media/sf_Downloads/SALDAS_temp_3m/','average')
#aggregateRastersQuarterly('/media/sf_Downloads/SALDAS_evap_mm/','/media/sf_Downloads/SALDAS_evap_3m/','average')
#aggregateRastersQuarterly('/media/sf_Downloads/SALDAS_EvapMonthly/','/media/sf_Downloads/SALDAS_EvapQuarterly/','average')
