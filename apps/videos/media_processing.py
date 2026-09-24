import os
import tempfile
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError


def _video_path(video_file):
    if hasattr(video_file, 'path'):
        try:
            path = video_file.path
            if os.path.exists(path):
                return path, None
        except (NotImplementedError, AttributeError):
            pass

    suffix = Path(video_file.name).suffix or '.mp4'
    temporary = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        for chunk in video_file.chunks():
            temporary.write(chunk)
    finally:
        temporary.close()
    return temporary.name, temporary.name


def extract_video_metadata(video_file):
    try:
        import cv2
    except ImportError as exc:
        raise ValidationError(
            'Video metadata processing requires opencv-python-headless.'
        ) from exc

    path, temporary_path = _video_path(video_file)
    capture = cv2.VideoCapture(path)
    try:
        if not capture.isOpened():
            raise ValidationError('The uploaded video could not be read.')

        fps = capture.get(cv2.CAP_PROP_FPS)
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        if not fps or fps <= 0 or frame_count < 0:
            raise ValidationError('The uploaded video duration could not be determined.')

        duration_seconds = max(0, round(frame_count / fps))
        frame_ok, frame = capture.read()
        if not frame_ok or frame is None:
            raise ValidationError('A thumbnail frame could not be extracted from the uploaded video.')

        success, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 88])
        if not success:
            raise ValidationError('A thumbnail could not be generated from the uploaded video.')

        minutes, seconds = divmod(duration_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        duration = f'{hours}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes:02d}:{seconds:02d}'
        return duration, ContentFile(encoded.tobytes(), name='thumbnail.jpg')
    finally:
        capture.release()
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
