#!/usr/bin/env python3
"""
WebSocketストリーミング音声文字起こしAPIのデモクライアント

使用例:
  python demo_streaming.py audio.wav
  python demo_streaming.py audio.wav --model tiny --host localhost --port 8000
"""

import argparse
import asyncio
import json
import wave
import websockets
import httpx
from pathlib import Path
from typing import AsyncGenerator


async def check_model_status(host: str, port: int, model: str) -> dict:
    """モデルの準備状態を確認"""
    url = f"http://{host}:{port}/models/{model}/status"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {
            "model": model,
            "is_ready": False,
            "is_loaded": False,
            "message": f"Cannot connect to API server at {host}:{port}",
        }
    except httpx.HTTPStatusError as e:
        return {
            "model": model,
            "is_ready": False,
            "is_loaded": False,
            "message": f"HTTP error {e.response.status_code}: {e.response.text}",
        }
    except Exception as e:
        return {
            "model": model,
            "is_ready": False,
            "is_loaded": False,
            "message": f"Error checking model status: {str(e)}",
        }


async def play_audio_file(file_path: Path) -> None:
    """音声ファイルをスピーカーから再生"""
    try:
        # paplayを使用してWAVファイルを再生（PulseAudio）
        process = await asyncio.create_subprocess_exec(
            "paplay",
            str(file_path),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )

        print(f"🔊 音声再生開始: {file_path.name}")

        _, stderr = await process.communicate()

        if process.returncode == 0:
            print("🔊 音声再生完了")
        else:
            print(f"⚠️  音声再生エラー: {stderr.decode()}")

    except FileNotFoundError:
        print("⚠️  paplayが見つかりません。音声再生をスキップします")
    except Exception as e:
        print(f"⚠️  音声再生エラー: {e}")


async def read_audio_file(
    file_path: Path, chunk_size: int = 4096
) -> AsyncGenerator[bytes, None]:
    """音声ファイルを読み込んでチャンクごとに送信"""
    try:
        with wave.open(str(file_path), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()

            print("音声ファイル情報:")
            print(f"  チャンネル数: {channels}")
            print(f"  サンプル幅: {sample_width} bytes")
            print(f"  サンプルレート: {sample_rate} Hz")
            print(f"  フレーム数: {wav_file.getnframes()}")
            print(f"  再生時間: {wav_file.getnframes() / sample_rate:.2f} 秒")
            print()

            # サンプルレートに応じてチャンクサイズを調整
            # 約0.128秒分のデータになるように計算
            frames_per_chunk = int(sample_rate * 0.128)  # 128ms
            bytes_per_frame = sample_width * channels
            adjusted_chunk_size = frames_per_chunk * bytes_per_frame

            print(
                f"  調整後チャンクサイズ: {adjusted_chunk_size} bytes ({frames_per_chunk} frames)"
            )
            print()

            # WAVデータを読み込み
            while True:
                chunk = wav_file.readframes(frames_per_chunk)
                if not chunk:
                    break
                yield chunk
                # リアルな音声再生をシミュレート（少し待機）
                await asyncio.sleep(0.1)

    except wave.Error as e:
        print(f"WAVファイル読み込みエラー: {e}")
        raise
    except FileNotFoundError:
        print(f"ファイルが見つかりません: {file_path}")
        raise


async def stream_transcription(
    file_path: Path,
    host: str = "localhost",
    port: int = 8000,
    model: str = "base",
    language: str = "ja",
    play_audio: bool = False,
) -> None:
    """WebSocketでストリーミング文字起こしを実行"""

    print("🔍 モデル状態確認中...")
    model_status = await check_model_status(host, port, model)

    if not model_status["is_ready"]:
        print(f"❌ モデル '{model}' は準備できていません")
        print(f"   理由: {model_status['message']}")
        return

    if model_status["is_loaded"]:
        print(f"✅ モデル '{model}' は既にロード済みです")
    else:
        print(f"⏳ モデル '{model}' は利用可能ですが、初回実行時にロードされます")
        print("   初回のみ時間がかかる場合があります")

    url = f"ws://{host}:{port}/stream-transcribe?model={model}&language={language}"
    print(f"接続先: {url}")
    print(f"使用モデル: {model}")
    print(f"言語: {language}")
    print("=" * 50)

    try:
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket接続成功")

            # 準備完了メッセージを受信
            ready_message = await websocket.recv()
            ready_data = json.loads(ready_message)

            if ready_data.get("type") == "ready":
                print("📡 サーバー準備完了")
                print()
            else:
                print(f"❌ 予期しないメッセージ: {ready_data}")
                return

            # 音声データを送信するタスク
            async def send_audio():
                try:
                    # 最初に音声ファイル情報を送信
                    with wave.open(str(file_path), "rb") as wav_file:
                        audio_info = {
                            "type": "audio_info",
                            "sample_rate": wav_file.getframerate(),
                            "channels": wav_file.getnchannels(),
                            "sample_width": wav_file.getsampwidth(),
                        }
                        await websocket.send(json.dumps(audio_info))
                        print(
                            f"📋 音声情報送信: {wav_file.getframerate()}Hz, {wav_file.getnchannels()}ch"
                        )

                    async for chunk in read_audio_file(file_path):
                        await websocket.send(chunk)
                        ## print(f"📤 音声チャンク送信 ({len(chunk)} bytes)")

                    # 終了メッセージを送信
                    end_message = {"type": "end"}
                    await websocket.send(json.dumps(end_message))
                    print("🔚 終了メッセージ送信")

                except Exception as e:
                    print(f"❌ 音声送信エラー: {e}")

            # メッセージを受信するタスク
            async def receive_messages():
                audio_task = None
                first_partial_received = False

                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)

                        if data.get("type") == "partial":
                            # 最初の部分結果を受信したら音声再生を開始
                            if not first_partial_received and play_audio:
                                first_partial_received = True
                                audio_task = asyncio.create_task(
                                    play_audio_file(file_path)
                                )
                                print("🎵 モデル準備完了 - 音声再生開始")

                        print(
                            f"🔄 部分結果 (chunk {data.get('chunk_id', '?')}): {data.get('text', '')}"
                        )
                        if data.get("type") == "partial":
                            pass
                        elif data.get("type") == "final":
                            print()
                            print("=" * 50)
                            print("✅ 最終結果:")
                            print(f"言語: {data.get('language', 'unknown')}")
                            print(f"モデル: {data.get('model_used', 'unknown')}")
                            print("=" * 50)
                            break

                        elif data.get("type") == "error":
                            print(f"❌ エラー: {data.get('message', 'Unknown error')}")
                            break

                        else:
                            print(f"❓ 不明なメッセージ: {data}")

                    # 音声再生タスクが開始されていれば完了を待つ
                    if audio_task:
                        await audio_task

                except websockets.exceptions.ConnectionClosed:
                    print("🔌 WebSocket接続が閉じられました")
                except Exception as e:
                    print(f"❌ メッセージ受信エラー: {e}")
                finally:
                    # 音声再生タスクをキャンセル（必要に応じて）
                    if audio_task and not audio_task.done():
                        audio_task.cancel()

            # 送信と受信を並行実行（音声再生はreceive_messages内で制御）
            await asyncio.gather(send_audio(), receive_messages())

    except websockets.exceptions.InvalidURI:
        print(f"❌ 無効なURL: {url}")
    except (ConnectionRefusedError, OSError):
        print(
            f"❌ 接続拒否: {host}:{port} - APIサーバーが起動していることを確認してください"
        )
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="WebSocketストリーミング音声文字起こしAPIのデモクライアント",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s audio.wav
  %(prog)s audio.wav --model tiny --language en
  %(prog)s audio.wav --host 192.168.1.100 --port 8080
  %(prog)s audio.wav --model base --language ja --chunk-size 8192
  %(prog)s audio.wav --play-audio --language ja
        """,
    )

    parser.add_argument("audio_file", type=Path, help="音声ファイルのパス (WAV形式)")

    parser.add_argument(
        "--model", "-m", default="base", help="使用するWhisperモデル (default: base)"
    )

    parser.add_argument(
        "--language", "-l", default="ja", help="音声の言語コード (default: ja)"
    )

    parser.add_argument(
        "--host", default="localhost", help="APIサーバーのホスト (default: localhost)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="APIサーバーのポート (default: 8000)",
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4096,
        help="音声チャンクサイズ (bytes) (default: 4096)",
    )

    parser.add_argument(
        "--play-audio",
        action="store_true",
        help="音声ファイルをスピーカーから同時再生する",
    )

    args = parser.parse_args()

    # 入力ファイルの存在確認
    if not args.audio_file.exists():
        print(f"❌ ファイルが見つかりません: {args.audio_file}")
        return 1

    if not args.audio_file.suffix.lower() == ".wav":
        print(f"❌ WAVファイルを指定してください: {args.audio_file}")
        return 1

    print("🎵 WebSocketストリーミング音声文字起こしデモ")
    print(f"📁 ファイル: {args.audio_file}")

    try:
        asyncio.run(
            stream_transcription(
                args.audio_file,
                args.host,
                args.port,
                args.model,
                args.language,
                args.play_audio,
            )
        )
        return 0
    except KeyboardInterrupt:
        print("\n⏹️  ユーザーによって中断されました")
        return 1
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
