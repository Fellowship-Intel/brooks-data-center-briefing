from __future__ import annotations

from pathlib import Path
import sys
import traceback

from tts.gemini_tts import synthesize_speech


def main() -> None:
    print("🔊 Validating Gemini TTS...")

    test_text = "Hello Michael, this is a direct test of the Gemini text to speech setup."
    output_dir = Path("artifacts/tts_validation")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "gemini_tts_test.wav"

    try:
        audio_bytes = synthesize_speech(test_text, output_path=str(output_path))
    except Exception as exc:
        print("❌ Gemini TTS validation failed.")
        print(f"Error: {exc}")
        traceback.print_exc()
        sys.exit(1)

    if not audio_bytes:
        print("❌ synthesize_speech returned empty audio bytes.")
        sys.exit(1)

    if not output_path.exists() or output_path.stat().st_size == 0:
        print("❌ Output WAV file not created or is empty.")
        print(f"Expected at: {output_path}")
        sys.exit(1)

    print("✅ Gemini TTS validation succeeded.")
    print(f"   Test audio file: {output_path.resolve()}")


if __name__ == "__main__":
    main()

