# BLDAS - SLDAS Data viewer and Visualizer

This app is created to run in the [Tethys Platform Environment](https://github.com/tethysplatform/tethys) [(Documentation)](http://docs.tethysplatform.org/en/latest/)

## Prerequisites:

* Tethys Platform (CKAN, PostgresQL, GeoServer)
* rasterio
* rasterstats
* xarray

## Install Tathys Platform

See: http://docs.tethysplatform.org/en/latest/installation.html

## Install Dependencies

### Automatic

The below dependencies will be installed when you run the following command

```bash
python setup.py develop
```

## API Usage

### GetForecast for Forecasts Data

| Parameter | Description            | Example       | 
| ----------- | --------------- | --------- | 
| watershed_name OP     | CREATE          | READ      | 
| subbasin_name       | C dogs | List dogs |
| river_id  | River/Stream ID           | 2345678   | 
| return_format       | Currently only csv is supported | css |
| units  | Set to ‘english’ to get ft3/s. (Optional)           | english   | 

Example
```python
>>> import requests
>>> request_params = dict(watershed_name='Nepal', subbasin_name='Central', river_id=5,  return_format='csv')
>>> request_headers = dict(Authorization='Token asdfqwer1234')
>>> res = requests.get('[HOST Portal]/apps/bldas-explorer//api/GetForecast/', params=request_params, headers=request_headers)
```
##

## Future Planned Changes
* Expansion of API to support more methods and data as they come in.

## Changelog

## [Unreleased]

### Added

* Dependencies to setup.py
* LIS Data reader and visualization as forecast
* Layer for nepal drainage lines
* ReadMe
* API for Streamflow Data

### Changed

* gitignore cleanup

## [1.0.0] - 2018/08/14

### Added

* Initial Commit