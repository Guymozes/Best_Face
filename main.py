from flask import Flask
from flask import request
import requests
from operator import itemgetter

app = Flask(__name__)

subscription_key = "1322bb46d34d4b35aeea5d39589f43df"
assert subscription_key

face_api_url = 'https://bestfacedetection.cognitiveservices.azure.com/face/v1.0/detect'
api_face_similar = "https://eastus.api.cognitive.microsoft.com/face/v1.0/findsimilars"

headers = {'Ocp-Apim-Subscription-Key': subscription_key}

faces_dict = {}


@app.route("/")
def home():
    invalid_urls = set()
    params = {
        'returnFaceId': 'true',
        'returnFaceLandmarks': 'false'
    }
    entry_msg = "Please add URLs of images in the URL in the next format: /?list_of_images={url1},{url2} and so on"
    list_of_images = request.args.get('list_of_images').split(',') if request.args.get('list_of_images') else []
    if not list_of_images:
        return entry_msg
    for image_url in list_of_images:
        try:
            res = requests.post(face_api_url, params=params,
                                headers=headers, json={"url": image_url}).json()
            if 'error' in res:
                print(f"Error with {image_url}: {res['error']['message']}")
                invalid_urls.add(image_url)
                continue
            update_faces(res, image_url)
        except Exception as e:
            print(f"Error while calling the face api with: {image_url}.\nThe error: {e}")
    return find_best_face() + (f"<br/>Handled only valid urls.Invalid URLs: {invalid_urls}" if invalid_urls else '')


def find_best_face():
    prefix_msg_response = "The best face is from: "
    backup_msg = "Please insert valid URLs"
    res = prefix_msg_response + f"{(max(faces_dict.values(), key=itemgetter(1)))[2]}" if faces_dict else backup_msg
    return res


def update_faces(faces, image_url):
    for face in faces:
        face_id = face['faceId']
        similar_face_id = face_id
        face_size = calculate_size_of_face(face)
        similar_faces = find_similar_faces(face_id)
        if similar_faces:
            for similar_face in similar_faces:
                similar_face_id = similar_face['faceId']
                bigger_face_size = face_size > faces_dict[similar_face_id][1]
                faces_dict[similar_face_id] = (
                    faces_dict[similar_face_id][0] + 1,
                    face_size if bigger_face_size else faces_dict[similar_face_id][1],
                    image_url if bigger_face_size else faces_dict[similar_face_id][2])

        else:
            faces_dict[similar_face_id] = (1, face_size, image_url)


def find_similar_faces(face_id):
    res = []
    face_ids = [face for face in list(faces_dict.keys())]
    if face_ids:
        body = {
            "faceId": face_id,
            "faceIds": face_ids
        }
        res = requests.post(api_face_similar, headers=headers, json=body).json()
    return res


def calculate_size_of_face(face):
    face_rectangle = face['faceRectangle']
    return face_rectangle['height'] * face_rectangle['width']


if __name__ == "__main__":
    app.run(debug=True)
