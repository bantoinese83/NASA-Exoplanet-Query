import pandas as pd
from flask import Flask, render_template, request
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

def load_exoplanet_data(file_path):
    try:
        dtype = {col: 'str' for col in range(312)}
        data = pd.read_csv(file_path, dtype=dtype, low_memory=False)
        logging.info(f"Columns in CSV: {data.columns.tolist()}")

        if 'DATE' in data.columns:
            data['DATE'] = pd.to_datetime(data['DATE'], errors='coerce')
            data['DATE'] = data['DATE'].dt.year
            data['DATE'] = data['DATE'].fillna(0).astype(int)
            logging.info("Exoplanet data loaded successfully.")
        else:
            logging.error("Error: 'DATE' column not found in the CSV.")
            return pd.DataFrame()

        return data
    except FileNotFoundError:
        logging.error(f"Error: {file_path} not found.")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"An error occurred while loading the CSV: {e}")
        return pd.DataFrame()

exoplanet_data = load_exoplanet_data("static/exoplanets.csv")

def search_exoplanets(query_params, data):
    df = data.copy()
    for key, value in query_params.items():
        if value:
            df = df[df[key] == value]
    return df

def create_table_data(df):
    columns = ['DATE', 'PLANETDISCMETH', 'NAME', 'STAR']
    return df[columns].to_dict('records')

def get_query_params():
    return {
        'DATE': request.form.get('discovery_year'),
        'PLANETDISCMETH': request.form.get('discovery_method'),
        'NAME': request.form.get('host_name'),
        'STAR': request.form.get('discovery_facility'),
    }

def get_filter_options(data):
    return {
        'discovery_years': sorted(data['DATE'].unique()) if 'DATE' in data.columns else [],
        'discovery_methods': sorted(data['PLANETDISCMETH'].dropna().unique()) if 'PLANETDISCMETH' in data.columns else [],
        'host_names': sorted(data['NAME'].dropna().unique()) if 'NAME' in data.columns else [],
        'discovery_facilities': sorted(data['STAR'].dropna().unique()) if 'STAR' in data.columns else []
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    query_params = get_query_params()
    valid_params = {k: v for k, v in query_params.items() if v}

    sort_column = request.args.get('sort')
    sort_order = request.args.get('order', 'asc')

    if request.method == 'POST' and valid_params:
        results = search_exoplanets(valid_params, exoplanet_data)
        if sort_column:
            results = results.sort_values(by=sort_column, ascending=(sort_order == 'asc'))
        table_data = create_table_data(results)
        has_results = True
    else:
        table_data = []
        has_results = False

    filter_options = get_filter_options(exoplanet_data)

    return render_template('index.html',
                           discovery_years=filter_options['discovery_years'],
                           discovery_methods=filter_options['discovery_methods'],
                           host_names=filter_options['host_names'],
                           discovery_facilities=filter_options['discovery_facilities'],
                           table_data=table_data,
                           has_results=has_results,
                           query_params=query_params)

if __name__ == '__main__':
    app.run(debug=True)