import base64
import numpy as np

import cv2
from pyzbar import pyzbar


def detect_bcode(b64_str: str) -> str:
    """
    returns the first barcode detected in a base64 encoded image
    else None
    """
    encoded_img = b64_str.split(",")[1]
    img_arr = np.frombuffer(base64.b64decode(encoded_img), np.uint8)
    img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    # cv2.imwrite("test_img.png", img) -- test

    decoded_objects = pyzbar.decode(img)
    if len(decoded_objects) < 1:
        return None
    else:
        return decoded_objects[0].data.decode('utf-8')
