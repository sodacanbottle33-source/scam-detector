import cv2
from PIL import Image
from transformers import pipeline

MODEL_NAME = "prithivMLmods/Deep-Fake-Detector-v2-Model"

_detector = None


def _load_detector():
    global _detector

    if _detector is None:
        print("Loading AI video detector...")

        _detector = pipeline(
            "image-classification",
            model=MODEL_NAME
        )


def detect_ai_video(video_path, frame_count=10):
    _load_detector()

    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        return {
            "is_likely_ai": None,
            "error": "Could not open the video."
        }

    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        capture.release()
        return {
            "is_likely_ai": None,
            "error": "The video has no readable frames."
        }

    step = max(total_frames // frame_count, 1)

    ai_scores = []
    analyzed_frames = 0

    for frame_number in range(0, total_frames, step):
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        success, frame = capture.read()

        if not success:
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)

        predictions = _detector(image)

        for prediction in predictions:
            label = prediction["label"].lower()
            score = float(prediction["score"])

            if "deepfake" in label or "fake" in label:
                ai_scores.append(score)
                break

            if "real" in label or "realism" in label:
                ai_scores.append(1 - score)
                break

        analyzed_frames += 1

        if analyzed_frames >= frame_count:
            break

    capture.release()

    if not ai_scores:
        return {
            "is_likely_ai": None,
            "error": "The model could not classify the video frames."
        }

    average_ai_score = sum(ai_scores) / len(ai_scores)
    ai_confidence = round(average_ai_score * 100, 2)

    if average_ai_score >= 0.85:
        verdict = "Very Likely AI"
    elif average_ai_score >= 0.65:
        verdict = "Likely AI"
    elif average_ai_score >= 0.40:
        verdict = "Uncertain"
    else:
        verdict = "Likely Real"

    return {
        "verdict": verdict,
        "is_likely_ai": average_ai_score > 0.5,
        "ai_confidence": ai_confidence,
        "frames_analyzed": analyzed_frames
    }


if __name__ == "__main__":
    print("AI Video Detector Ready")