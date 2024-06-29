import streamlit as st
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
import plotly.graph_objects as go
from google.cloud import storage
import io
import csv

target_bucket="new_suzano_spare"
utc_difference=7

def gcp_download_x(bucket_name, source_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    data = blob.download_as_bytes()

    # Convert bytes to a file-like object
    data_io = io.StringIO(data.decode('utf-8'))
    reader = csv.reader(data_io)

    # Convert CSV data to a list of tuples
    elevation_list = [tuple(row) for row in reader]
    return elevation_list
def read_csv_to_list_of_lists(file_path):
    with open(file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        elevation_list = [list(row) for row in reader]
    return elevation_list    
def gcp_download(bucket_name, source_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_file_name)
    data = blob.download_as_text()
    return data
    
def load_data():
    with rasterio.open('terminal.tif') as src:
        geo_bounds = (-122.90612, 47.05128, -122.89835, 47.05930)
        raster_bounds = transform_bounds('EPSG:4326', src.crs, *geo_bounds, densify_pts=21)
        window = src.window(*raster_bounds)
        elevation_data = src.read(1, window=window)
        nodata_value = src.nodata if src.nodata else -3.402823e+38
        elevation_data = np.where(elevation_data == nodata_value, np.nan, elevation_data)
        elevation_data = elevation_data[:, ::-1]
    return elevation_data

def plot_elevation(elevation_data, max_tide):
    min_elevation = np.nanmin(elevation_data[elevation_data > -1000])
    max_elevation = np.nanmax(elevation_data)
    mllw = -4.470
    mhhw = mllw + 14.56
    fig = go.Figure(data=[go.Surface(z=elevation_data, cmin=min_elevation, cmax=max_elevation, colorscale='Earth')])
    fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mllw), showscale=False, opacity=0.5, colorscale=[[0, 'blue'], [1, 'blue']]))
    fig.add_trace(go.Surface(z=np.full(elevation_data.shape, mhhw), showscale=False, opacity=0.5, colorscale=[[0, 'red'], [1, 'red']]))
    fig.add_trace(go.Surface(z=np.full(elevation_data.shape, max_tide), showscale=False, opacity=0.5, colorscale=[[0, 'green'], [1, 'green']]))
    fig.update_layout(title='Marine Terminal Elevation with Tidal Levels',
                      autosize=True,
                      scene=dict(zaxis=dict(title='Elevation (feet)', range=[-7, max_elevation + 10]),
                                 camera=dict(eye=dict(x=1.87, y=0.88, z=-0.64))),
                      margin=dict(l=65, r=50, b=65, t=90))
    return fig
elevation_data=gcp_download_x(target_bucket,rf"elevation.csv")
#elevation_data = load_data()
#elevation_data = read_csv_to_list_of_lists(elevation_data)
st.write(elevation_data)
st.title("Marine Terminal Elevation Viewer")
max_tide = st.slider("Select Maximum Tide Level (feet)", float(-4.47), float(30.0), float(18.4))
st.plotly_chart(plot_elevation(elevation_data, max_tide))
