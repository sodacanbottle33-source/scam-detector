import gc

MODEL_NAME = "prithivMLmods/Deep-Fake-Detector-v2-Model"


def detect_ai_video(video_path, frame_count=10):
    detector = None
    capture = None

    try:
        import cv2
        from PIL import Image
        from transformers import pipeline

        print("Loading AI video detector on demand...")

        detector = pipeline(
            "image-classification",
            model=MODEL_NAME,
            device=-1,
        )

        capture = cv2.VideoCapture(video_path)

        if not capture.isOpened():
            return {
                "is_likely_ai": None,
                "error": "Could not open the video.",
            }

        total_frames = int(
            capture.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        if total_frames <= 0:
            return {
                "is_likely_ai": None,
                "error": "The video has no readable frames.",
            }

        step = max(total_frames // frame_count, 1)

        ai_scores = []
        analyzed_frames = 0

        for frame_number in range(0, total_frames, step):
            capture.set(
                cv2.CAP_PROP_POS_FRAMES,
                frame_number,
            )

            success, frame = capture.read()

            if not success:
                continue

            frame_rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB,
            )

            image = Image.fromarray(frame_rgb)
            predictions = detector(image)

            frame_score = None

            for prediction in predictions:
                label = str(
                    prediction["label"]
                ).lower()

                score = float(
                    prediction["score"]
                )

                if (
                    "deepfake" in label
                    or "fake" in label
                ):
                    frame_score = score
                    break

                if (
                    "real" in label
                    or "realism" in label
                ):
                    frame_score = 1 - score
                    break

            if frame_score is not None:
                ai_scores.append(frame_score)

            analyzed_frames += 1

            if analyzed_frames >= frame_count:
                break

        if not ai_scores:
            return {
                "is_likely_ai": None,
                "error": (
                    "The model could not classify "
                    "the video frames."
                ),
            }

        average_ai_score = (
            sum(ai_scores) / len(ai_scores)
        )

        ai_confidence = round(
            average_ai_score * 100,
            2,
        )

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
            "frames_analyzed": analyzed_frames,
        }

    except Exception as error:
        return {
            "is_likely_ai": None,
            "error": (
                f"{type(error).__name__}: {error}"
            ),
        }

    finally:
        if capture is not None:
            try:
                capture.release()
            except Exception:
                pass

        detector = None
        gc.collect()


if __name__ == "__main__":
    print("AI Video Detector Ready")