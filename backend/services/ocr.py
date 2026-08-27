import pytesseract
from PIL import Image


def recognize_text(image):

    text = pytesseract.image_to_string(
        image,
        lang="pol+eng"
    )

    return text



#.