import streamlit as st
import pandas as pd
import plotly.express as px

COLUMNS_MAP = {
    "Zeit": "Time",
    "Saldo vor": "Balance Before",
    "Saldo nach": "Balance After",
    "Aktion": "Action",
    # Zeit,Saldo vor,Saldo nach,P&L,Aktion
    # Time,Balance Before,Balance After,P&L,Action
}

def plot(df, inital_equity=100_000):
    fig = px.line(df, x='Time', y='Equity')
    fig.update_layout(xaxis_tickangle=-75)
    fig.add_hline(y=inital_equity, line_dash='dash', line_color='gray')
    fig.update_traces(mode='lines+markers')
    fig.update_xaxes(tickformat='%Y-%m-%d')
    fig.update_yaxes(tickformat='.0f')
    return fig

def analyze_df(df_account_history):
    #df_account_history = pd.read_csv(data)
    # check if a specific column exists
    if 'Balance After' not in df_account_history.columns:
        df_account_history.rename(columns=COLUMNS_MAP, inplace=True)
    df_account_history['Time'] = pd.to_datetime(df_account_history['Time'])
    df_account_history.rename(columns={"Balance After": "Equity"}, inplace=True)
    df_account_history.drop(columns=['Balance Before'], inplace=True)
    df_account_history = df_account_history.sort_values('Time', ascending=True).reset_index(drop=True)
    df_account_history.index.name = 'Trade #'

    return df_account_history

def test_and_read_csv(uploaded_file, ignore_first_trade):
    """Test if the uploaded file is a valid CSV file with the expected columns."""

    example_data_en ="""
    Time,Balance Before,Balance After,P&L,Action
    2023-05-15 09:00:10,99018.85222294275,98931.90515197215,-86.9470709705929,"Close long position for symbol EUREX:FGBL1! at price 135.76 for 2 shares. Position AVG Price was 135.800000, currency: EUR, rate: 1.086838, last updated rate on 2023-05-15T05:42:52Z, point value: 1000.000000"
    2023-05-12 08:48:57,98668.85222294279,99018.85222294275,349.99999999995634,"Close short position for symbol CME:6E1! at price 1.09525 for 2 shares. Position AVG Price was 1.096650, currency: USD, point value: 125000.000000"
    """
    example_data_de ="""
    Zeit,Saldo vor,Saldo nach,P&L,Aktion
    2024-04-29 01:53:05,98931.90515197215,98545.88756672663,-386.0175852455286,"Close short position for symbol EUREX:FGBLM2024 at price 130.76 for 1 shares. Position AVG Price was 130.400000, currency: EUR, rate: 1.072271, last updated rate on 2024-04-29T08:24:10Z, point value: 1000.000000"
    2023-05-14 23:00:10,99018.85222294275,98931.90515197215,-86.9470709705929,"Close long position for symbol EUREX:FGBL1! at price 135.76 for 2 shares. Position AVG Price was 135.800000, currency: EUR, rate: 1.086838, last updated rate on 2023-05-15T05:42:52Z, point value: 1000.000000"
    """

    EXPECTED_COLUMNS_DE = ["Zeit", "Saldo vor", "Saldo nach", "P&L", "Aktion"]
    EXPECTED_COLUMNS_EN = ["Time", "Balance Before", "Balance After", "P&L", "Action"]
    
    try:
        _df = pd.read_csv(uploaded_file)
        en_columns_match = all(col.lower() in _df.columns.str.lower() for col in EXPECTED_COLUMNS_EN)
        de_columns_match = all(col.lower() in _df.columns.str.lower() for col in EXPECTED_COLUMNS_DE)
        if not (en_columns_match or de_columns_match):
            st.write('***ERROR:*** Columns do not match the expected format. Please check the file.')
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
        return _df
    return pd.DataFrame()


st.set_page_config(page_title="TV Equity", layout="centered", initial_sidebar_state="auto")#

uploaded_file = st.file_uploader('Upload TradingView CSV export file (Account History/"Kontoverlauf") to analyze equity curve:', type="csv")

ignore_first_trade = st.toggle('Ignore first trade for calculations.', value=True)
if not ignore_first_trade:
    st.write('***Notice:*** Calculations include the first trade.')

if uploaded_file is not None:
    df = test_and_read_csv(uploaded_file, ignore_first_trade)
    df = analyze_df(df)

    if len(df) < 1:
        st.write('***ERROR:*** No Trade data in the uploaded file.')
        st.stop()

    if ignore_first_trade:
        df = df.iloc[1:]
        df = df.sort_values('Time', ascending=True).reset_index(drop=True)
        df.index.name = 'Trade #'

    inital_equity=df['Equity'][0]
    final_equity=df['Equity'].iloc[-1]
    st.write('Initial Equity:', inital_equity)
    st.write('Final Equity:', final_equity)


    st.header('Equity Curve:')
    fig = plot(df, inital_equity=inital_equity)
    st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit")

    st.write('Total Performance:', (final_equity - inital_equity)/inital_equity*100, '%' )
    # Equity performance


    st.header('P&L of each trade:')
    st.write('Total P&L:', final_equity - inital_equity)
    st.bar_chart(df['P&L'])

    st.header('Trade details:')
    st.dataframe(df, use_container_width=True)

