#!/usr/bin/env python3
"""
テスト用の音声ファイルを作成するスクリプト
"""

import wave
import math
import struct
from pathlib import Path


def create_test_wav(
    filename: str, duration: float = 3.0, sample_rate: int = 16000
) -> Path:
    """テスト用のWAVファイルを作成"""
    file_path = Path(filename)
    frames = int(sample_rate * duration)

    with wave.open(str(file_path), "wb") as wav_file:
        wav_file.setnchannels(1)  # モノラル
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # 複数の周波数のサイン波を重ねた音声を生成
        audio_data = []
        for i in range(frames):
            # 440Hz（A音）と880Hz（A音1オクターブ上）を混合
            value1 = 0.3 * math.sin(2 * math.pi * 440 * i / sample_rate)
            value2 = 0.2 * math.sin(2 * math.pi * 880 * i / sample_rate)
            # 音量変化（フェードイン・フェードアウト）
            fade_factor = min(i / (sample_rate * 0.1), 1.0)  # 0.1秒でフェードイン
            fade_factor = min(
                fade_factor, (frames - i) / (sample_rate * 0.1)
            )  # 0.1秒でフェードアウト

            combined_value = int(32767 * fade_factor * (value1 + value2))
            audio_data.append(struct.pack("<h", combined_value))

        wav_file.writeframes(b"".join(audio_data))

    return file_path


if __name__ == "__main__":
    # 短いテスト用音声ファイルを作成
    test_file = create_test_wav("test_audio.wav", duration=2.0)
    print(f"テスト音声ファイルを作成しました: {test_file}")

    # ファイル情報を表示
    with wave.open(str(test_file), "rb") as wav_file:
        print(f"チャンネル数: {wav_file.getnchannels()}")
        print(f"サンプル幅: {wav_file.getsampwidth()} bytes")
        print(f"サンプルレート: {wav_file.getframerate()} Hz")
        print(f"フレーム数: {wav_file.getnframes()}")
        print(f"再生時間: {wav_file.getnframes() / wav_file.getframerate():.2f} 秒")
        print(f"ファイルサイズ: {test_file.stat().st_size} bytes")
