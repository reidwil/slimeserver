import os
import streamlit as st
from fitparse import FitFile
import pandas as pd
from datetime import datetime

# Directory containing .fit files
ACTIVITIES_DIR = os.path.join(os.path.dirname(__file__), 'activities')

# Caching for parsing .fit files
@st.cache_data(show_spinner=False)
def parse_fit_file_cached(filepath):
    mtime = os.path.getmtime(filepath)
    fitfile = FitFile(filepath)
    data = []
    for record in fitfile.get_messages('record'):
        record_data = {}
        for field in record:
            record_data[field.name] = field.value
        data.append(record_data)
    return data, mtime

# Helper to parse a .fit file and extract summary info (uncached, for legacy use)
def parse_fit_file(filepath):
    fitfile = FitFile(filepath)
    data = []
    for record in fitfile.get_messages('record'):
        record_data = {}
        for field in record:
            record_data[field.name] = field.value
        data.append(record_data)
    return data

# Caching for DataFrame creation for map viewer
@st.cache_data(show_spinner=False)
def get_map_df(filepath):
    records, mtime = parse_fit_file_cached(filepath)
    if not records:
        return None
    df = pd.DataFrame(records)
    # Extract latitude and longitude columns (fitparse uses semicircles, sometimes needs conversion)
    lat_cols = [col for col in df.columns if 'lat' in col]
    lon_cols = [col for col in df.columns if 'lon' in col]
    lat_col = next((c for c in lat_cols if 'position_lat' in c), lat_cols[0] if lat_cols else None)
    lon_col = next((c for c in lon_cols if 'position_long' in c or 'position_lon' in c), lon_cols[0] if lon_cols else None)
    if lat_col and lon_col:
        # Convert from semicircles to degrees if needed
        if df[lat_col].max() > 90 or df[lat_col].min() < -90:
            df['lat'] = df[lat_col] * (180 / 2**31)
            df['lon'] = df[lon_col] * (180 / 2**31)
        else:
            df['lat'] = df[lat_col]
            df['lon'] = df[lon_col]
        map_df = df[['lat', 'lon']].dropna()
        return df, map_df
    return df, None

# List all .fit files
def get_fit_files():
    return [f for f in os.listdir(ACTIVITIES_DIR) if f.endswith('.fit')]

# Helper to extract summary for an activity
def extract_activity_summary(filepath):
    records = parse_fit_file(filepath)
    if not records:
        return None
    df = pd.DataFrame(records)
    # Try to extract summary metrics
    summary = {}
    summary['file'] = os.path.basename(filepath)
    if 'timestamp' in df.columns:
        summary['start_time'] = pd.to_datetime(df['timestamp'].iloc[0])
    else:
        summary['start_time'] = None
    for col in ['distance', 'total_distance']:
        if col in df.columns:
            summary['distance'] = df[col].max()
            break
    else:
        summary['distance'] = None
    # Average speed, ignoring zeros
    for col in ['speed', 'enhanced_speed']:
        if col in df.columns:
            speeds = df[col]
            speeds = speeds[speeds > 0]
            summary['avg_speed'] = speeds.mean() if not speeds.empty else None
            break
    else:
        summary['avg_speed'] = None
    for col in ['heart_rate', 'enhanced_heart_rate']:
        if col in df.columns:
            summary['avg_hr'] = df[col].mean()
            break
    else:
        summary['avg_hr'] = None
    if 'timestamp' in df.columns:
        summary['duration'] = (pd.to_datetime(df['timestamp'].iloc[-1]) - pd.to_datetime(df['timestamp'].iloc[0])).total_seconds()
    else:
        summary['duration'] = None
    # Round all numeric metrics to 2 decimals
    for k in ['distance', 'avg_speed', 'avg_hr', 'duration']:
        if summary[k] is not None:
            summary[k] = round(summary[k], 2)
    return summary

# Set Weekly Aggregation as the main page
if 'page' not in st.session_state:
    st.session_state['page'] = 'Weekly Aggregation'

page = st.session_state.get('page', 'Weekly Aggregation')

# Ensure Route Map Viewer page is present in sidebar and logic is included
sidebar_pages = ['Weekly Aggregation', 'Route Map Viewer']
selected_sidebar_page = st.sidebar.selectbox('Select Page', sidebar_pages, index=sidebar_pages.index(page) if page in sidebar_pages else 0)
if selected_sidebar_page != page:
    st.session_state['page'] = selected_sidebar_page
    st.rerun()
page = selected_sidebar_page

if page == 'Route Map Viewer':
    st.title('Route Map Viewer')
    fit_files = get_fit_files()
    # Build display names for each file: filename (name, sport) if available
    file_display = []
    file_info = []
    from fitparse import FitFile
    for fname in fit_files:
        fpath = os.path.join(ACTIVITIES_DIR, fname)
        try:
            fitfile = FitFile(fpath)
            name = None
            sport = None
            # Try to get activity name from session or activity message
            for msg in fitfile.get_messages('session'):
                name = msg.get_value('event') or msg.get_value('activity_name') or msg.get_value('name')
                sport = msg.get_value('sport')
                if name or sport:
                    break
            if not name:
                for msg in fitfile.get_messages('activity'):
                    name = msg.get_value('activity_name') or msg.get_value('name')
                    if name:
                        break
            display = fname
            if name or sport:
                display += ' ('
                if name:
                    display += str(name)
                if name and sport:
                    display += ', '
                if sport:
                    display += str(sport)
                display += ')'
            file_display.append(display)
            file_info.append((fname, display))
        except Exception:
            file_display.append(fname)
            file_info.append((fname, fname))
    # Map display name back to filename
    display_to_file = {display: fname for fname, display in file_info}
    selected_display = st.selectbox('Select a FIT file to view route', file_display, key='route_map_file')
    selected_file = display_to_file[selected_display] if selected_display else None
    if selected_file:
        filepath = os.path.join(ACTIVITIES_DIR, selected_file)
        st.write(f'Parsing: {selected_file}')
        try:
            # Use cached DataFrame for map viewer
            df_map, map_df = get_map_df(filepath)
            if df_map is not None and map_df is not None and not map_df.empty:
                import pydeck as pdk
                # Create path for the route
                path = map_df[['lon', 'lat']].values.tolist()
                # PathLayer for the route
                path_layer = pdk.Layer(
                    "PathLayer",
                    data=[{"path": path}],
                    get_path="path",
                    get_color='[0, 100, 255]',
                    width_scale=10,
                    width_min_pixels=3,
                )
                # Add start marker (green) and end marker (red)
                marker_data = []
                if path:
                    marker_data.append({"lon": path[0][0], "lat": path[0][1], "label": "Start", "color": [0, 200, 0]})
                    marker_data.append({"lon": path[-1][0], "lat": path[-1][1], "label": "Finish", "color": [200, 0, 0]})
                marker_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=marker_data,
                    get_position='[lon, lat]',
                    get_color='[color]',
                    get_radius=40,
                    pickable=True,
                )
                layers = [path_layer, marker_layer]
                view_state = pdk.ViewState(
                    longitude=map_df['lon'].mean(),
                    latitude=map_df['lat'].mean(),
                    zoom=13,
                    pitch=0
                )
                st.pydeck_chart(pdk.Deck(
                    layers=layers,
                    initial_view_state=view_state,
                    tooltip={"text": "{label}"}
                ))
                # Show styled metrics at the bottom
                if 'distance' in df_map.columns:
                    distance_miles = df_map['distance'].max() * 0.000621371
                else:
                    distance_miles = None
                hr_col = next((c for c in df_map.columns if 'heart_rate' in c), None)
                avg_hr = df_map[hr_col].mean() if hr_col else None
                if 'timestamp' in df_map.columns:
                    t0 = pd.to_datetime(df_map['timestamp'].iloc[0])
                    t1 = pd.to_datetime(df_map['timestamp'].iloc[-1])
                    total_seconds = (t1 - t0).total_seconds()
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)
                    duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                else:
                    duration_str = None
                st.markdown("""
                    <style>
                    .metric-card {
                        border: 2px solid #222;
                        border-radius: 12px;
                        background: #222831;
                        padding: 1.2em 0.5em 0.5em 0.5em;
                        margin: 0.5em;
                        text-align: center;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.10);
                    }
                    .metric-label {
                        color: #bfc6d1;
                        font-size: 1em;
                        margin-bottom: 0.2em;
                    }
                    .metric-value {
                        color: #fff;
                        font-size: 1.5em;
                        font-weight: bold;
                    }
                    </style>
                """, unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Distance</div><div class="metric-value">{distance_miles:.2f} mi</div></div>' if distance_miles is not None else '<div class="metric-card"><div class="metric-label">Distance</div><div class="metric-value">-</div></div>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Avg Heart Rate</div><div class="metric-value">{avg_hr:.0f} bpm</div></div>' if avg_hr is not None else '<div class="metric-card"><div class="metric-label">Avg Heart Rate</div><div class="metric-value">-</div></div>', unsafe_allow_html=True)
                with col3:
                    st.markdown(f'<div class="metric-card"><div class="metric-label">Duration</div><div class="metric-value">{duration_str}</div></div>' if duration_str else '<div class="metric-card"><div class="metric-label">Duration</div><div class="metric-value">-</div></div>', unsafe_allow_html=True)
            else:
                st.warning('No latitude/longitude data found in this file.')
        except Exception as e:
            st.error(f'Error parsing file: {e}')

elif page == 'Weekly Aggregation':
    st.title('Weekly Aggregation of Activities')
    st.markdown('''
        ## Weekly Metrics Overview
        The diagrams below show your weekly activity trends, including total distance (in miles), average speed, average heart rate, total duration, and activity count. Use these charts to spot trends, improvements, or changes in your training over time. Quick stats below give you a snapshot of your recent activity.
    ''')
    fit_files = get_fit_files()
    summaries = []
    for f in fit_files:
        filepath = os.path.join(ACTIVITIES_DIR, f)
        summary = extract_activity_summary(filepath)
        if summary:
            summaries.append(summary)
    if summaries:
        df = pd.DataFrame(summaries)
        # Drop activities without a start_time
        df = df.dropna(subset=['start_time'])
        df['week'] = df['start_time'].dt.to_period('W').apply(lambda r: r.start_time)
        agg = df.groupby('week').agg(
            total_distance=pd.NamedAgg(column='distance', aggfunc='sum'),
            avg_speed=pd.NamedAgg(column='avg_speed', aggfunc='mean'),
            avg_hr=pd.NamedAgg(column='avg_hr', aggfunc='mean'),
            total_duration=pd.NamedAgg(column='duration', aggfunc='sum'),
            activity_count=pd.NamedAgg(column='file', aggfunc='count')
        ).reset_index()
        # Convert total_distance from meters to miles, round to 2 decimals
        if 'total_distance' in agg.columns:
            agg['total_distance_miles'] = (agg['total_distance'] * 0.000621371).round(2)
        # Convert total_duration from seconds to hours, round to 2 decimals
        if 'total_duration' in agg.columns:
            agg['total_duration_hours'] = (agg['total_duration'] / 3600).round(2)
        # Round all other metrics to 2 decimals
        for col in ['avg_speed', 'avg_hr']:
            if col in agg.columns:
                agg[col] = agg[col].round(2)
        # Quick stats for the past 7 days
        last_7_days = df[df['start_time'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
        miles_7d = last_7_days['distance'].sum() * 0.000621371 if not last_7_days.empty else 0
        hours_7d = last_7_days['duration'].sum() / 3600 if not last_7_days.empty else 0
        st.columns(1)  # force new row
        col1, col2 = st.columns(2)
        col1.metric('Miles in the past 7 days', f"{miles_7d:.2f}")
        col2.metric('Total hours in the past 7 days', f"{hours_7d:.2f}")
        st.subheader('Weekly Metrics')
        import altair as alt
        # Date slider for week range
        # Convert week to datetime for slider compatibility
        if pd.api.types.is_period_dtype(agg['week']):
            agg['week_dt'] = agg['week'].dt.to_timestamp()
        else:
            agg['week_dt'] = pd.to_datetime(agg['week'])
        # Convert to native Python datetime
        agg['week_dt'] = agg['week_dt'].apply(lambda x: x.to_pydatetime() if hasattr(x, 'to_pydatetime') else x)
        week_min = agg['week_dt'].min()
        week_max = agg['week_dt'].max()
        # Force min/max/value to be native datetime.datetime
        import datetime
        if isinstance(week_min, pd.Timestamp):
            week_min = week_min.to_pydatetime()
        if isinstance(week_max, pd.Timestamp):
            week_max = week_max.to_pydatetime()
        week_range = st.slider(
            'Select week range to display:',
            min_value=week_min,
            max_value=week_max,
            value=(week_min, week_max),
            format='YYYY-MM-DD'
        )
        # Filter agg by selected week range
        agg_filtered = agg[(agg['week_dt'] >= week_range[0]) & (agg['week_dt'] <= week_range[1])]
        metrics = [
            ('Total Distance (miles)', 'total_distance_miles', '#1f77b4'),
            ('Average Speed', 'avg_speed', '#ff7f0e'),
            ('Average Heart Rate', 'avg_hr', '#2ca02c'),
            ('Total Duration (hours)', 'total_duration_hours', '#d62728'),
            ('Activity Count', 'activity_count', '#9467bd'),
        ]
        for label, col, color in metrics:
            if col in agg_filtered.columns:
                st.subheader(label, divider='rainbow')
                chart = alt.Chart(agg_filtered).mark_line(color=color, point=True).encode(
                    x=alt.X('week_dt:T', title='Week'),
                    y=alt.Y(f'{col}:Q', title=label)
                ).properties(
                    width='container',
                    height=250
                )
                st.altair_chart(chart, use_container_width=True)
        st.subheader('Weekly Data Table')
        st.dataframe(agg_filtered)
    else:
        st.write('No activity summaries available.') 