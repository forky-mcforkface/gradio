import os

import numpy as np

import gradio as gr


def reverse_audio(audio):
    sr, data = audio
    return (sr, np.flipud(data))


demo = gr.Interface(fn=reverse_audio, 
                    inputs="microphone", 
                    outputs="audio", 
                    examples=[
                    os.path.join(os.path.dirname(__file__), "audio/cantina.wav"),
                    os.path.join(os.path.dirname(__file__), "audio/recording1.wav")
        ], cache_examples=True)

if __name__ == "__main__":
    demo.launch()
