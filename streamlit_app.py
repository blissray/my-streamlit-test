import os
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from twilio.rest import Client
import toml

# Read Twilio account information from config.toml
account_sid = st.secrets["twilio"]["account_sid"]
auth_token = st.secrets["twilio"]["auth_token"]


# Twilio 클라이언트 초기화
client = Client(account_sid, auth_token)

def get_ice_servers():
    token = client.tokens.create()
    return token.ice_servers

print(get_ice_servers())
from streamlit_webrtc import webrtc_streamer
import av


def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")

    flipped = img[::-1,:,:]

    return av.VideoFrame.from_ndarray(flipped, format="bgr24")


webrtc_streamer(
    key="example",
    rtc_configuration={
        "iceServers": get_ice_servers()
    },

    video_frame_callback=video_frame_callback)