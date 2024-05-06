import logging
import queue

import matplotlib.pyplot as plt
import numpy as np
import pydub
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

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


logger = logging.getLogger(__name__)


webrtc_ctx = webrtc_streamer(
    key="sendonly-audio",
    mode=WebRtcMode.SENDONLY,
    audio_receiver_size=256,
    rtc_configuration={"iceServers": get_ice_servers()},
    media_stream_constraints={"audio": True},
)

fig_place = st.empty()

fig, [ax_time, ax_freq] = plt.subplots(2, 1, gridspec_kw={"top": 1.5, "bottom": 0.2})

sound_window_len = 5000  # 5s
sound_window_buffer = None
while True:
    if webrtc_ctx.audio_receiver:
        try:
            audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
        except queue.Empty:
            logger.warning("Queue is empty. Abort.")
            break

        sound_chunk = pydub.AudioSegment.empty()
        for audio_frame in audio_frames:
            sound = pydub.AudioSegment(
                data=audio_frame.to_ndarray().tobytes(),
                sample_width=audio_frame.format.bytes,
                frame_rate=audio_frame.sample_rate,
                channels=len(audio_frame.layout.channels),
            )
            sound_chunk += sound

        if len(sound_chunk) > 0:
            if sound_window_buffer is None:
                sound_window_buffer = pydub.AudioSegment.silent(
                    duration=sound_window_len
                )

            sound_window_buffer += sound_chunk
            if len(sound_window_buffer) > sound_window_len:
                sound_window_buffer = sound_window_buffer[-sound_window_len:]

        if sound_window_buffer:
            # Ref: https://own-search-and-study.xyz/2017/10/27/python%E3%82%92%E4%BD%BF%E3%81%A3%E3%81%A6%E9%9F%B3%E5%A3%B0%E3%83%87%E3%83%BC%E3%82%BF%E3%81%8B%E3%82%89%E3%82%B9%E3%83%9A%E3%82%AF%E3%83%88%E3%83%AD%E3%82%B0%E3%83%A9%E3%83%A0%E3%82%92%E4%BD%9C/  # noqa
            sound_window_buffer = sound_window_buffer.set_channels(1)  # Stereo to mono
            sample = np.array(sound_window_buffer.get_array_of_samples())

            ax_time.cla()
            times = (np.arange(-len(sample), 0)) / sound_window_buffer.frame_rate
            ax_time.plot(times, sample)
            ax_time.set_xlabel("Time")
            ax_time.set_ylabel("Magnitude")

            spec = np.fft.fft(sample)
            freq = np.fft.fftfreq(sample.shape[0], 1.0 / sound_chunk.frame_rate)
            freq = freq[: int(freq.shape[0] / 2)]
            spec = spec[: int(spec.shape[0] / 2)]
            spec[0] = spec[0] / 2

            ax_freq.cla()
            ax_freq.plot(freq, np.abs(spec))
            ax_freq.set_xlabel("Frequency")
            ax_freq.set_yscale("log")
            ax_freq.set_ylabel("Magnitude")

            fig_place.pyplot(fig)
    else:
        logger.warning("AudioReciver is not set. Abort.")
        break