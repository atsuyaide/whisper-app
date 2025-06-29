#!/usr/bin/env python3
"""
日本語音声を模した音声ファイルを作成するスクリプト
（実際の音声ではなく、特定の周波数パターンを模擬）
"""

import wave
import math
import struct
from pathlib import Path


def create_speech_like_wav(
    filename: str, duration: float = 3.0, sample_rate: int = 16000
) -> Path:
    """音声を模したWAVファイルを作成"""
    file_path = Path(filename)
    frames = int(sample_rate * duration)

    with wave.open(str(file_path), "wb") as wav_file:
        wav_file.setnchannels(1)  # モノラル
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # 日本語の「こんにちは」を模した周波数パターン
        audio_data = []
        for i in range(frames):
            t = i / sample_rate

            # 時間に応じて周波数を変化させる（音声の抑揚を模擬）
            if t < 0.5:  # 「こ」
                freq = 200 + 50 * math.sin(2 * math.pi * 3 * t)
            elif t < 1.0:  # 「ん」
                freq = 150 + 30 * math.sin(2 * math.pi * 2 * t)
            elif t < 1.5:  # 「に」
                freq = 300 + 80 * math.sin(2 * math.pi * 4 * t)
            elif t < 2.0:  # 「ち」
                freq = 400 + 100 * math.sin(2 * math.pi * 5 * t)
            else:  # 「は」
                freq = 250 + 60 * math.sin(2 * math.pi * 3 * t)

            # 音量の変化（フェードイン・フェードアウト）
            fade_factor = min(t / 0.1, 1.0)  # 0.1秒でフェードイン
            fade_factor = min(
                fade_factor, (duration - t) / 0.1
            )  # 0.1秒でフェードアウト
            fade_factor = max(fade_factor, 0.0)

            # ランダムノイズを加えて音声らしさを演出
            noise = 0.1 * (0.5 - (i % 13) / 26.0)  # 疑似ランダムノイズ

            # 基本波形 + 倍音 + ノイズ
            value1 = 0.6 * math.sin(2 * math.pi * freq * t)
            value2 = 0.2 * math.sin(2 * math.pi * freq * 2 * t)  # 2倍音
            value3 = 0.1 * math.sin(2 * math.pi * freq * 3 * t)  # 3倍音

            combined_value = int(
                16384 * fade_factor * (value1 + value2 + value3 + noise)
            )
            combined_value = max(-32767, min(32767, combined_value))  # クリッピング防止

            audio_data.append(struct.pack("<h", combined_value))

        wav_file.writeframes(b"".join(audio_data))

    return file_path


if __name__ == "__main__":
    # 音声らしいテストファイルを作成
    speech_file = create_speech_like_wav("speech_demo.wav", duration=3.0)
    print(f"音声デモファイルを作成しました: {speech_file}")

    # ファイル情報を表示
    with wave.open(str(speech_file), "rb") as wav_file:
        print(f"チャンネル数: {wav_file.getnchannels()}")
        print(f"サンプル幅: {wav_file.getsampwidth()} bytes")
        print(f"サンプルレート: {wav_file.getframerate()} Hz")
        print(f"フレーム数: {wav_file.getnframes()}")
        print(f"再生時間: {wav_file.getnframes() / wav_file.getframerate():.2f} 秒")
        print(f"ファイルサイズ: {speech_file.stat().st_size} bytes")

    print("\n使用例:")
    print(f"uv run python streaming.py {speech_file} --play-audio --language ja")
