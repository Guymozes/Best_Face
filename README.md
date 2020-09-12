# Best_Face
Get best face via Azure APIs.
When activating the script, in order to recieve the desired result, please add URLs of images(JPEG, PNG, and BMP format are supported) in the URL in the next format:
/?list_of_images={url1},{url2} and so on.
The script will use Azure (via 2 APIs - detect and find similar) and return the best image (most common face out of the whole images) and between the images of this face, the one where the face is the largest.
In addition, it will also return the top and left position of that face in the image.
