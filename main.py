import argparse
import os

import cv2
import gfpgan
import insightface
import requests
from insightface.app import FaceAnalysis
from insightface.app.common import Face

MODELS: dict[str, str] = {
    "GFPGAN": "https://huggingface.co/henryruhs/roop/resolve/main/GFPGANv1.4.pth",
    "inswapper": "https://huggingface.co/henryruhs/roop/resolve/main/inswapper_128.onnx",
}

MODELS_DIR: str = "./models/"


def get_model_path(url: str) -> str:
    model_file = os.path.basename(url)
    return os.path.join(MODELS_DIR, model_file)


def download_model(url: str) -> None:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(get_model_path(url), "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def detect_face(face_analysis: FaceAnalysis, image: cv2.Mat) -> Face:
    faces = face_analysis.get(image)

    if len(faces) == 0:
        raise Exception("No faces detected")
    elif len(faces) > 1:
        raise Exception("Multiple faces detected")

    return faces[0]


def run(target: str, source: str, output: str, disable_enhance: bool) -> None:
    target_img = cv2.imread(target)
    source_img = cv2.imread(source)

    face_analysis = FaceAnalysis(name="buffalo_l")
    face_analysis.prepare(ctx_id=0, det_size=(640, 640))

    target_face = detect_face(face_analysis, target_img)
    source_face = detect_face(face_analysis, source_img)

    face_swapper = insightface.model_zoo.get_model(get_model_path(MODELS["inswapper"]))

    output_img = face_swapper.get(target_img, target_face, source_face, paste_back=True)

    if not disable_enhance:
        gfpganer = gfpgan.GFPGANer(model_path=get_model_path(MODELS["GFPGAN"]), upscale=1)
        _, _, output_img = gfpganer.enhance(output_img, paste_back=True)

    cv2.imwrite(output, output_img)


def main() -> None:
    parser = argparse.ArgumentParser("Face Swapper")
    parser.add_argument("-t", "--target", type=str, help="Target image path")
    parser.add_argument("-s", "--source", type=str, help="Source image path")
    parser.add_argument("-o", "--output", type=str, help="Output image path")
    parser.add_argument("-d", "--disable-enhance", action="store_true", help="Disable image enhancement")

    args = parser.parse_args()

    os.makedirs(MODELS_DIR, exist_ok=True)

    for model_url in MODELS.values():
        if not os.path.exists(get_model_path(model_url)):
            download_model(model_url)

    run(args.target, args.source, args.output, args.disable_enhance)


if __name__ == "__main__":
    main()
