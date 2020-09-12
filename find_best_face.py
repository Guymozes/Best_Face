from flask import Flask
from flask import request
import requests
from operator import itemgetter

app = Flask(__name__)

subscription_key = "1322bb46d34d4b35aeea5d39589f43df"
assert subscription_key

# API to detect faces in a given image
face_api_url = 'https://bestfacedetection.cognitiveservices.azure.com/face/v1.0/detect'

# API to check if one face is similar to others
api_face_similar = "https://eastus.api.cognitive.microsoft.com/face/v1.0/findsimilars"

headers = {'Ocp-Apim-Subscription-Key': subscription_key}
params = {
    'returnFaceId': 'true',
    'returnFaceLandmarks': 'false'
}


# Entry point
@app.route("/")
def home():
    invalid_urls = set()
    invalid_urls_msg = "<br/>Invalid URLs: "
    faces_dict = {}  # Key: face ids, value: tuple: (number of same person in all images, maximum face size,
    # url of image with maximum face size)
    entry_msg = "Please add URLs of images(JPEG, PNG, and BMP format are supported) in the URL in the next format: " \
                "/?list_of_images={url1},{url2} and so on"
    list_of_images = request.args.get('list_of_images').split(',') if request.args.get('list_of_images') else []
    if not list_of_images:
        return entry_msg
    for image_url in list_of_images:
        try:
            res = requests.post(face_api_url, params=params,
                                headers=headers, json={"url": image_url}).json()  # Call the face detect API
            if 'error' in res:
                print(f"Error with {image_url}: {res['error']['message']}")
                invalid_urls.add(image_url)
                continue
            update_faces(res, faces_dict, image_url)
        except Exception as e:
            print(f"Error while calling the face api with: {image_url}.\nThe error: {e}")
    # Return the invalid URL to the user (in case there are)
    invalid_urls_msg = f"{invalid_urls_msg} {','.join(invalid_urls)}" if invalid_urls else ''
    return find_best_face(faces_dict) + invalid_urls_msg


def update_faces(faces, faces_dict, image_url):
    """Updates the faces_dict with the correct values: the number of times the face appeared,
    maximum face size and the url of the image that has that maximum face size.
    Parameters:
           faces (list): A list of faces from the given image URL.
           faces_dict (dict): The dictionary of all the faces
           image_url (str): The url of the current image. """
    for face in faces:
        face_id = face['faceId']
        similar_face_id = face_id
        face_size = calculate_size_of_face(face)
        similar_faces = find_similar_faces(list(faces_dict.keys()), face_id)
        if similar_faces:
            for similar_face in similar_faces:
                similar_face_id = similar_face['faceId']
                bigger_face_size = face_size > faces_dict[similar_face_id][1]
                if bigger_face_size:
                    faces_dict[face_id] = (faces_dict[similar_face_id][0] + 1, face_size, image_url)
                    del faces_dict[similar_face_id]
                else:
                    current_values = faces_dict[similar_face_id]
                    faces_dict[similar_face_id] = (current_values[0] + 1, current_values[1], current_values[2])

        else:
            faces_dict[similar_face_id] = (1, face_size, image_url)


def find_similar_faces(face_ids_list, face_id):
    """Search for a similar face from the face ids in faces_dicts, using the API.
     The face_id will be compared to each face_id from the faces_dict keys and in case the API returns a value,
      it found a match. Else - no similar face.
    Parameters:
           face_id (str): The face id to search for similar faces.
           face_ids_list (list): A list of all the face ids"""
    res = []
    if face_ids_list:
        body = {
            "faceId": face_id,
            "faceIds": face_ids_list
        }
        res = requests.post(api_face_similar, headers=headers, json=body).json()
    return res


def calculate_size_of_face(face):
    """Calculates the size of the current face, based on the height and width of the API result.
    Parameters:
           face (dict): The current face to calculate the face size. """
    face_rectangle = face['faceRectangle']
    return face_rectangle['height'] * face_rectangle['width']


def find_best_face(faces_dict):
    """Return the best image with the best face - meaning the image,
     that has the most common face from all the images, that has the largest face size"""

    prefix_msg_response = "The best face is from:"
    no_valid_urls_msg = "Please insert valid URLs"
    if faces_dict:
        max_face_item = max(faces_dict.values(), key=itemgetter(1))  # Finds the image that is the common one,
        # and that has the largest face.
        max_face_image = max_face_item[2]

        # Call the face detect API in order to get the top and left position of the wanted face
        response = requests.post(face_api_url, params=params,
                            headers=headers, json={"url": max_face_image}).json()

        # Find the same face in the image of the best face and return with top and left position
        for face_id, face_values in faces_dict.items():
            if face_values == max_face_item:
                for face in response:
                    if face['faceId'] == face_id:
                        top, left = face['faceRectangle']['top'], face['faceRectangle']['left']
                        return f"{prefix_msg_response} {max_face_image}. The face top is: {top} and left: {left}"
    return no_valid_urls_msg


if __name__ == "__main__":
    app.run()
