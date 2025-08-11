import requests
import streamlit as st
import pandas as pd
from howlongtobeatpy import HowLongToBeat
import altair as alt



API_KEY = st.secrets["API_SECRET"]

def get_steam_id64(api_key, vanity_name):
    url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
    params = {'key': api_key, 'vanityurl': vanity_name}
    response = requests.get(url, params=params).json()
    if response['response']['success'] == 1:
        return response['response']['steamid']
    else:
        st.error(f"Could not resolve vanity URL: https://steamcommunity.com/id/{vanity_name}/")
        return None

@st.cache_data(show_spinner=False)
def get_owned_games(api_key, steam_id64):
    url = 'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/'
    params = {
        'key': api_key,
        'steamid': steam_id64,
        'include_appinfo': True,
        'include_played_free_games': True
    }
    response = requests.get(url, params=params).json()
    games = response['response'].get('games', [])
    return games

@st.cache_data(show_spinner=False)
def get_hltb_main_story(game_name):
    hltb = HowLongToBeat()
    results = hltb.search(game_name)
    if results:
        return results[0].main_story
    return None

st.title("🎮 Steam Dashboard")

vanity_name = st.text_input("Enter your Steam vanity URL") ## add info on how to find it

if vanity_name:
    with st.spinner("Resolving SteamID64..."):
        steam_id64 = get_steam_id64(API_KEY, vanity_name)

    if steam_id64:
        st.write(f"Your SteamID64: {steam_id64}")

        with st.spinner("Fetching owned games..."):
            games = get_owned_games(API_KEY, steam_id64)

        st.write(f"Found {len(games)} games in your library.")

        data = []
        progress_bar = st.progress(0)
        for i, game in enumerate(games):
            name = game.get('name', 'Unknown')
            playtime_hours = game.get('playtime_forever', 0) / 60  # minutes to hours
            hltb_time = get_hltb_main_story(name)

            data.append({
                'Game': name,
                'Playtime (hrs)': round(playtime_hours, 2),
                'How Long it takes to beat (hrs)': hltb_time
            })
            progress_bar.progress((i + 1) / len(games))

        df = pd.DataFrame(data)
        df = df.sort_values(by='Playtime (hrs)', ascending=False)
        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name='steam_hltb_dashboard.csv',
            mime='text/csv',
            
        )

    top_games = df.head(10)

    chart = alt.Chart(top_games).mark_bar().encode(
        x=alt.X('Playtime (hrs):Q', title='Playtime (hours)'),
        y=alt.Y('Game:N', sort='-x', title='Game'),
        tooltip=['Game', 'Playtime (hrs)', 'How Long it takes to beat (hrs)']
    ).properties(
        title='Top 10 Most Played Games',
        width=700,
        height=400
    )

    st.altair_chart(chart)

