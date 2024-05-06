import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
from twilio.rest import Client
import av
import logging

logger = logging.getLogger(__name__)

# Read Twilio account information from config.toml

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

@st.cache_data
def get_ice_servers():
    """Use Twilio's TURN server because Streamlit Community Cloud has changed
    its infrastructure and WebRTC connection cannot be established without TURN server now.  # noqa: E501
    We considered Open Relay Project (https://www.metered.ca/tools/openrelay/) too,
    but it is not stable and hardly works as some people reported like https://github.com/aiortc/aiortc/issues/832#issuecomment-1482420656  # noqa: E501
    See https://github.com/whitphx/streamlit-webrtc/issues/1213
    """

    # Ref: https://www.twilio.com/docs/stun-turn/api
    try:
        account_sid = st.secrets["account_sid"]
        auth_token = st.secrets["auth_token"]


        # Twilio 클라이언트 초기화
        client = Client(account_sid, auth_token)        
    except KeyError:
        logger.warning(
            "Twilio credentials are not set. Fallback to a free STUN server from Google."  # noqa: E501
        )
        return [{"urls": ["stun:stun.l.google.com:19302"]}]

    client = Client(account_sid, auth_token)

    token = client.tokens.create()

    return token.ice_servers

muted = st.checkbox("Mute")

from streamlit_webrtc import webrtc_streamer, VideoHTMLAttributes


webrtc_streamer(
    key="mute_sample",
    video_html_attrs=VideoHTMLAttributes(
        autoPlay=True, controls=True, style={"width": "100%"}, muted=muted
    ),
    rtc_configuration=get_ice_servers()
)
