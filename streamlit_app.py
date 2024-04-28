import streamlit_app as st
import pandas as pd
import plotly.express as px

def plot(df, inital_equity=100_000):
    fig = px.line(df, x='Time', y='Equity')
    fig.update_layout(xaxis_tickangle=-75)
    fig.add_hline(y=inital_equity, line_dash='dash', line_color='gray')
    fig.update_traces(mode='lines+markers')
    fig.update_xaxes(tickformat='%Y-%m-%d')
    fig.update_yaxes(tickformat='.0f')
    return fig

def analyze_df(data):
    df_account_history = pd.read_csv(data)
    df_account_history['Time'] = pd.to_datetime(df_account_history['Time'])
    df_account_history.rename(columns={"Balance After": "Equity"}, inplace=True)
    df_account_history.drop(columns=['Balance Before'], inplace=True)
    df_account_history = df_account_history.sort_values('Time', ascending=True).reset_index(drop=True)
    df_account_history.index.name = 'Trade #'

    return df_account_history


st.set_page_config(page_title="TV Equity", layout="centered", initial_sidebar_state="auto")

uploaded_file = st.file_uploader("Upload TV Account History CSV file:", type="csv")

ignore_first_trade = st.toggle('Ignore first trade for calculations.', value=True)
if not ignore_first_trade:
    st.write('***Notice:*** Calculations include the first trade.')

if uploaded_file is not None:
    df = analyze_df(uploaded_file)
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

