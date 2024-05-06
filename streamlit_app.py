import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from twilio.rest import Client
import av

# Read Twilio account information from config.toml
account_sid = st.secrets["account_sid"]
auth_token = st.secrets["auth_token"]


# Twilio 클라이언트 초기화
client = Client(account_sid, auth_token)

def get_ice_servers():
    token = client.tokens.create()
    return token.ice_servers



def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")

    flipped = img[::-1,:,:]

    return av.VideoFrame.from_ndarray(flipped, format="bgr24")


webrtc_streamer(
    key="example",

    video_frame_callback=video_frame_callback)