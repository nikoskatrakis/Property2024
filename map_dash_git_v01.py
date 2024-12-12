import dash
from dash import Dash, html, Output, Input, State, dcc, callback_context, ALL, MATCH
import dash_leaflet as dl
import pandas as pd
import numpy as np
from dash_extensions.javascript import assign
import matplotlib.colors as mcolors
import random
import datetime
import json

CENTER_LATITUDE = 51.5
CENTER_LONGITUDE = -0.10
BASE_ZOOM = 12

def calc_inflation_averages(df, start_year, end_year):
    # Filter columns based on the selected years
    inflation_columns = [str(year) for year in range(start_year, end_year + 1)]
    df.columns = [str(col).strip() for col in df.columns]
    # Check if the columns are present
    missing_columns = [col for col in inflation_columns if col not in df.columns]
    if missing_columns:
        print(f"Warning: The following year columns are missing from the data: {missing_columns}")
    
    # Calculate the average inflation for the selected years for each row
    df['period_inflation_rate'] = (df[inflation_columns].mean(axis=1, skipna=True)*100 ).fillna(0).round(2)
    df['period_inflation_rate_pc'] = df['period_inflation_rate'].apply(lambda x: f"{x:.2f}%")
    
    # Fill missing inflation values with the calculated average for the selected period
    df[inflation_columns] = df[inflation_columns].fillna(df['period_inflation_rate'], axis=0)

    df.columns = df.columns.map(lambda x: str(x) if isinstance(x, int) else x)

    year_columns = [str(year) for year in range(1995, 2025)]

    # Filter the DataFrame to make sure only existing columns are used
    existing_year_columns = [col for col in year_columns if col in df.columns]
    df = df.drop(columns=existing_year_columns)

    return df

#  Load data
merged_file = 'properties_small_detailed.csv' #'property_and_coords.csv' 
area_file = 'properties_small_area.csv' # 'area_inflation.csv' 

# merged_df_datalink = "https://drive.google.com/file/d/1iuJjd6XYl97GL0niY4VybWss998BZpS7/view?usp=sharing"
# area_data_datalink = "https://drive.google.com/file/d/1mDNmC-XtO8slKbT8fEIyqcj2gI53-Mj4/view?usp=sharing"

# # Download files from Google Drive 
# try: 
#     gdown.download(merged_df_datalink, merged_file, quiet=False) 
# except Exception as e: 
#     print(f"Failed to download {merged_file}: {e}") 
# try: 
#     gdown.download(area_data_datalink, area_file, quiet=False) 
# except Exception as e: 
#     print(f"Failed to download {area_file}: {e}")

area_data = pd.read_csv(area_file)
area_data_period = calc_inflation_averages(area_data, 1995, 2024)
merged_df = pd.read_csv(merged_file)


def on_click(event): print("Marker clicked!", event)

on_click = assign("""
    function(e, ctx) { 
        if (ctx && ctx.props) { 
            return { latlng: e.latlng, area: ctx.props.id }; // Directly return data to callback
        } 
        else { 
            console.log("Context is empty or missing properties. Returning null.");
            return null; // Return null if ctx is undefined or missing properties 
        }
    }
""")

def inflation_to_color(value):
    norm = mcolors.Normalize(vmin=0, vmax=20)  # aiming to capture 95% of observed inflation rates. 
    cmap = mcolors.LinearSegmentedColormap.from_list("", ["blue", "red"])
    return mcolors.to_hex(cmap(norm(value)))

def mytooltiptable(data_for_postcode):
    table = html.Table(
        # Header
        [html.Thead(
            html.Tr([html.Th(col, style={"position": "sticky", "top": "0", "backgroundColor": "#f8f9fa"}) for col in ["Postcode", "Street", "Flat", "Inflation rate","From","To","Most recent sale"]])
        )] +
        # Body
        [html.Tbody(
            [html.Tr([
                html.Td(data_for_postcode.iloc[i]["postcode"]),
                html.Td(data_for_postcode.iloc[i]["street"]),
                html.Td(data_for_postcode.iloc[i]["flat"]),
                html.Td(f'{data_for_postcode.iloc[i]["inflation_rate"] * 100:.2f}%', style={"textAlign": "right","width": "50px"}),
                html.Td(data_for_postcode.iloc[i]["earliest_date"]),
                html.Td(data_for_postcode.iloc[i]["most_recent_date"]),
                html.Td(f'{data_for_postcode.iloc[i]["most_recent_price"] / 1000:.1f}K', style={"textAlign": "right","width": "50px"}),
            ])
            for i in range(len(data_for_postcode))
            ]
        )],
        style={"width": "800px"}  # Ensure table uses full width
    )
    return html.Div(
        [table],
        style={"width": "100%", "maxHeight": "400px", "maxWidth": "800px", "overflowY": "scroll", "overflowX": "auto"}
    )

def detailed_data(year_range,thedf,postcode_area,widerange=True):
    start_year, end_year = year_range

    start_date = f"{start_year}-01-01"
    end_date = f"{end_year}-12-31"

    tempdata = thedf[thedf["postcode_area"] == postcode_area].copy()

    tempdata['temp_most_recent_date'] = pd.to_datetime(tempdata['most_recent_date'], format='%d/%m/%Y')
    tempdata['temp_earliest_date'] = pd.to_datetime(tempdata['earliest_date'], format='%d/%m/%Y')

    if widerange:
        mydf = tempdata[
            (tempdata['temp_most_recent_date'] >= start_date) &
            (tempdata['temp_earliest_date'] <= end_date)
                ].sort_values(by=["street", "flat"])
    else:    
        mydf = tempdata[
            (tempdata['temp_most_recent_date'] <= end_date) &
            (tempdata['temp_earliest_date'] >= start_date)
                ].sort_values(by=["street", "flat"])


    mydf = mydf.drop(columns=['temp_most_recent_date', 'temp_earliest_date'])

    mydf = mydf.dropna(subset=['lat'])

    return mydf

# Create initial markers
initial_markers = []
for index, row in area_data_period.iterrows():
    marker_id = {'type': 'marker', 'index': row["postcode_area"]}
    color = inflation_to_color(row["period_inflation_rate"])
    marker = dl.CircleMarker( 
        center=[row["lat"], row["long"]], 
        color=color, 
        radius=10, 
        fill=True, 
        fillColor=color, 
        fillOpacity=0.6,
        children=dl.Tooltip(html.Div([
            html.Span(f"Postcode area: {row['postcode_area']}"), 
            html.Br(),
            html.Span(f"Average Inflation Rate: {row['period_inflation_rate']}%")
        ])),
        id = marker_id,  # Ensure id is properly set
        eventHandlers={"click": on_click}  # ,  # Ensure click event handler is set
    )
    initial_markers.append(marker)

# Dash app setup
app = Dash(__name__)

app.layout = html.Div([
    dcc.Store(id='marker-ids', data=[marker.id for marker in initial_markers]),
    dcc.RangeSlider(id='year-slider', min=1995, max=2024, value=[1995, 2024], marks={year: str(year) for year in range(1995, 2025)}, step=1, allowCross=False),
    html.Button('Update Map', id='update-button', n_clicks=0),
    dl.Map(children=[dl.TileLayer()] + initial_markers, style={'width': '100%', 'height': '80vh'}, center=[CENTER_LATITUDE, CENTER_LONGITUDE], zoom = BASE_ZOOM, id="map"),
    html.Div(id="output", style={"padding": "20px", "fontSize": "16px"}),
])


@app.callback(
    [Output("map", "children"),
     Output("output", "children"),
     Output("map", "center"),
     Output("map", "zoom"),
     Output('marker-ids', 'data')],
    [Input("update-button", "n_clicks"),
     Input({'type': 'marker', 'index': ALL}, 'n_clicks')],
    [State("year-slider", "value"), State("map", "children"), State('marker-ids', 'data')]
)
def update_map_and_handle_clicks(n_clicks, *args):
    year_slider_value = args[-3]
    map_children = args[-2]
    current_marker_ids = args[-1]
    click_counts = args[:-3]

    ctx = dash.callback_context
    # print("ctx:", ctx)
    # print("slider values:", year_slider_value)
    # print("ctx.triggered:", ctx.triggered)
    # print("map_childen: (first 3):", map_children[:3])
    # print("current marker ids (first 3):", current_marker_ids[:3])

    # Check if the update button was clicked
    if ctx.triggered and 'update-button.n_clicks' in ctx.triggered[0]['prop_id']:
        # print("just jumped into the summary markers update")
        start_year, end_year = year_slider_value
        area_data_period = calc_inflation_averages(area_data, start_year, end_year)

        center = (CENTER_LATITUDE, CENTER_LONGITUDE)
        zoom = BASE_ZOOM  # Initial zoom level

        # Create new markers based on the updated data
        new_initial_markers = []
        for index, row in area_data_period.iterrows():
#            marker_id = row["postcode_area"] + "_" + str(n_clicks)
            marker_id = {'type': 'marker', 'index': row["postcode_area"] + "_" + str(n_clicks)}
            color = inflation_to_color(row["period_inflation_rate"])
            marker = dl.CircleMarker(
                center=[row["lat"], row["long"]],
                color= color,
                radius=10,
                fill=True,
                fillColor=color,
                fillOpacity=0.6,
                children=dl.Tooltip(html.Div([
                    html.Span(f"Postcode area: {row['postcode_area']}"),
                    html.Br(),
                    html.Span(f"Average Inflation Rate: {row['period_inflation_rate']}%")
                ])),
                id = marker_id,
                eventHandlers = {"click": on_click}
            )
            new_initial_markers.append(marker)

        current_marker_ids = [marker.id for marker in new_initial_markers]

        # print("Updated Marker IDs (first 3):", current_marker_ids[:3]) 
        # print("Updated Map Children (first 3):", new_initial_markers[:3])

        return [dl.TileLayer()] + new_initial_markers, "Map updated with new data!", center, zoom, current_marker_ids

    # Handle marker clicks
    if ctx.triggered and any(marker_id['index'].split('_')[0] in ctx.triggered[0]['prop_id'].split('.')[0] for marker_id in current_marker_ids):
#        print("just jumped into the detailed markers loop")
        children = map_children
        clicked_marker_id = ctx.triggered[0]['prop_id'].split('.')[0]
        mymarker = json.loads(clicked_marker_id)
#        print("my marker:", mymarker['index'])
        if not clicked_marker_id:
            return children, "No marker click detected!", dash.no_update, dash.no_update, current_marker_ids
        clicked_marker_id = mymarker['index']
        if '_' in clicked_marker_id: clicked_marker_id = clicked_marker_id.split('_')[0]

#        print("clicked marker id: ", clicked_marker_id)
        new_markers_data = detailed_data(year_slider_value,merged_df,clicked_marker_id, False)

        mylong = area_data[area_data['postcode_area']==clicked_marker_id]['long']
        mylat = area_data[area_data['postcode_area']==clicked_marker_id]['lat']
#        print('lon, lat:' , np.float32(mylong), np.float32(mylat))
        
        if new_markers_data.empty:
#            print("you did something and I ended up in the if new_merkers_data.empty line")
            return children, "No data read", dash.no_update, dash.no_update, current_marker_ids

        unq_postcodes = new_markers_data['postcode'].unique().tolist()
        new_markers = []

        for postcode in unq_postcodes:
            if len(new_markers_data[new_markers_data['postcode'] == postcode]) == 1:
                row = new_markers_data[new_markers_data['postcode'] == postcode].iloc[0]
                color = inflation_to_color(row["inflation_rate"] * 100)
                marker = dl.CircleMarker(
                    center=[row["lat"], row["long"]],
                    color=color,
                    radius=5,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6,
                    children=dl.Tooltip(html.Div([
                        html.Span(f"Postcode: {row['postcode']}"),
                        html.Br(),
                        html.Span(f"Street: {row['street']}"),
                        html.Br(),
                        html.Span(f"Flat: {row['flat']}"),
                        html.Br(),
                        html.Span(f"Inflation rate: {round(row['inflation_rate'] * 100, 2)}%"),
                        html.Br(),
                        html.Span(f"From: {row['earliest_date']}"),
                        html.Br(),
                        html.Span(f"To: {row['most_recent_date']}"),
                        html.Br(),
                        html.Span(f"Most recent sale: {round(row['most_recent_price'] / 1000, 1)}K"),
                    ])),
#                    id=f"{row['postcode']}-{row['street']}-{row['flat']}"
                    id={'type': 'marker', 'index': f"{row['postcode']}-{row['street']}-{row['flat']}"}
                )
            else:
                pcrows = new_markers_data[new_markers_data['postcode'] == postcode]
                anyrow = pcrows.iloc[1]
                new_inflation_rate = round(pcrows['inflation_rate'].mean() * 100, 2)
                color = inflation_to_color(new_inflation_rate)
                marker = dl.CircleMarker(
                    center=[anyrow["lat"], anyrow["long"]],
                    color=color,
                    radius=5,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6,
                    children=dl.Popup(mytooltiptable(pcrows), maxWidth=800),
                    id=f"{anyrow['postcode']}"
                )
            new_markers.append(marker)
        

        updated_children = [dl.TileLayer()] + initial_markers + new_markers

        center =  [float(mylat), float(mylong)]  #  [float(np.mean(latitudes)), float(np.mean(longitudes))]
        zoom = 15
#        print("printing detailed markers . . . ")
        return updated_children, f"Added {len(new_markers)} markers for Postcode Area: {clicked_marker_id}.", center, zoom, current_marker_ids

#    print("whatever you did, did not have an effect . . . ")
    return map_children, dash.no_update, dash.no_update, dash.no_update, current_marker_ids


if __name__ == '__main__': 
    app.run_server(debug=False, host='0.0.0.0', port=8050)