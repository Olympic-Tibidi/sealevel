import streamlit as st
import geemap.foliumap as geemap
import ee
from streamlit_folium import folium_static
ee.Initialize(ee.ServiceAccountCredentials(
    st.secrets.json_data,
    key_data=st.secrets.private_key))
ee.Authenticate()
rise=1
"""
This is a Streamlit web app for visualizing areas impacted by rising sea level.
"""


#st.set_page_config(page_title="8 lines code demo", page_icon="🤖")

st.write("# Rising Sea Level impact (2050) on lands in red")

DEMO_CODE = """
ee.Initialize(ee.ServiceAccountCredentials(
    st.secrets.gee_service_account,
    key_data=st.secrets.gee_service_account_credentials))

# create map centered on hong kong with district level zoom
m = geemap.Map(center=(22.30, 114.1694), zoom=14, basemap="HYBRID")
dem = ee.Image("NASA/NASADEM_HGT/001")
impacted_land = dem.expression(
    "(elevation < 0.3) && (swb == 0)",
    {'elevation': dem.select('elevation'),
     'swb': dem.select('swb')})
viz_params = {'min': 0, 'max': 1, 'palette': ['000000', 'FF0000'],
              'opacity': 0.4}

m.addLayer(impacted_land, viz_params, 'impacted areas')
m.addLayerControl()

# render folium map
folium_static(m)
"""

#st.code(DEMO_CODE, language="python", line_numbers=False)

# ee.Initialize(ee.ServiceAccountCredentials(
#     st.secrets.gee_service_account,
#     key_data=st.secrets.gee_service_account_credentials))

# create map centered on hong kong with district level zoom
m = geemap.Map(center=(47.0534, -122.90167), zoom=14, basemap="HYBRID")
dem = ee.Image("NASA/NASADEM_HGT/001")
impacted_land = dem.expression(
    f"(elevation < {rise}) && (swb == 0)",
    {'elevation': dem.select('elevation'),
     'swb': dem.select('swb')})
viz_params = {'min': 0, 'max': 1, 'palette': ['000000', 'FF0000'],
              'opacity': 0.4}

m.addLayer(impacted_land, viz_params, 'impacted areas')
m.addLayerControl()

# render folium map
folium_static(m)
display(m)
