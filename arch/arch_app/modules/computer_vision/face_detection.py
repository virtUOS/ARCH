import cv2
import cvlib  # see https://www.cvlib.net/


def detect_faces(image_path):
    """ Detect faces on an image. """
    img_raw = cv2.imread(image_path)                # load image
    img = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)  # correct color coding
    faces, confidences = cvlib.detect_face(img)     # detect faces
    return faces


# alternative face detection using haar cascade classifier

# classifier = cv2.CascadeClassifier(
#     cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
# )
#
# def detect_faces(image_path):
#     """ Detect faces on an image. """
#     img_raw = cv2.imread(image_path)  # load image
#     # min_size = (int(img_raw.shape[0] / 50), int(img_raw.shape[1] / 50))  # set minimal face size based on image size
#     gray_image = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)  # set color coding to gray
#     faces = classifier.detectMultiScale(
#         gray_image, scaleFactor=1.05, minNeighbors=7, minSize=(35, 35)
#     )
#     face_coordinates = []
#     for face in faces:
#         x1, y1, width, height = face
#         x2, y2 = x1 + width, y1 + height
#         face_coordinates.append((x1, y1, x2, y2))
#     return face_coordinates
