from django.shortcuts import render
import requests
import pytesseract
from PIL import Image
from django.core.files.storage import FileSystemStorage
import hashlib
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.crypto import get_random_string
from django.conf import settings  # Import settings

#index
def index(request):
    return render(request, 'Apps/index.html')

#Weather
def weather(request):
    if request.method == "POST":
        city = request.POST['city']
        api_key = 'cb92c2105916474a94d60338242112'  # Your WeatherAPI key
        url = f'http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}&aqi=no'

        # Make the API request
        response = requests.get(url)
        data = response.json()

        if 'error' not in data:  # Check if there's an error in the response
            # Extract weather data
            weather_data = {
                'temperature': data['current']['temp_c'],  # Temperature in Celsius
                'pressure': data['current']['pressure_mb'],  # Pressure in mb
                'humidity': data['current']['humidity'],  # Humidity in %
                'description': data['current']['condition']['text'],  # Weather description
                'city': city
            }
            return render(request, 'Apps/weather.html', {'weather_data': weather_data})
        else:
            error_message = "City not found or invalid API key."
            return render(request, 'Apps/weather.html', {'error_message': error_message})

    return render(request, 'Apps/weather.html')


#ocr
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path to where Tesseract is installed

def ocr(request):
    extracted_text = ''

    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_file = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_url = fs.url(filename)

        # Use pytesseract to extract text from the uploaded image
        img = Image.open(fs.path(filename))
        extracted_text = pytesseract.image_to_string(img)

        return render(request, 'Apps/ocr.html', {'file_url': file_url, 'extracted_text': extracted_text})

    return render(request, 'Apps/ocr.html')

dynamic_storage = {}


#md5

def md5(request):
    hash_value = None
    original_string = None

    if request.method == "POST":
        # Handle MD5 Hash Generation
        if "generate_hash" in request.POST:
            text = request.POST.get("text")
            if text:
                hash_value = hashlib.md5(text.encode()).hexdigest()
                # Save the text and its hash for reverse lookup
                dynamic_storage[hash_value] = text
        
        # Handle MD5 to Original String Conversion
        elif "get_original" in request.POST:
            md5_hash = request.POST.get("md5")
            if md5_hash:
                original_string = dynamic_storage.get(md5_hash, "Original string not found")

    return render(request, 'Apps/md5.html', {
        'hash_value': hash_value,
        'original_string': original_string,
    })



#nearby finder
def nearby(request):
    if request.method == "POST":
        city = request.POST.get('city')
        place = request.POST.get('place')

        if not city or not place:
            return render(request, 'Apps/nearby.html', {'error_message': 'City and Place fields are required.'})

        # Nominatimm API URL for searching places within the city
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={place}+in+{city}&limit=20"

        headers = {
            "User-Agent": "NearbyApp/1.0 (ramakrishnant684@gmail.com)"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Check for HTTP errors
            data = response.json()

            if not data:
                return render(request, 'Apps/nearby.html', {'error_message': 'No nearby places found.'})

            places = []
            for place_data in data:
                full_name = place_data['display_name']
                
                # Extract only the place name (first part before a comma)
                name = full_name.split(',')[0]

                # Use the full address
                address = full_name

                lat = place_data['lat']
                lon = place_data['lon']

                # Prepare the Google Maps link for each place
                google_map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"

                # Add place data
                places.append({
                    "name": name,
                    "address": address,
                    "google_map_link": google_map_link
                })

            if not places:
                return render(request, 'Apps/nearby.html', {'error_message': f'No places found for "{place}" in {city}.'})

            return render(request, 'Apps/nearby.html', {'places': places, 'place': place, 'city': city})

        except requests.exceptions.RequestException as e:
            return render(request, 'Apps/nearby.html', {'error_message': f"Error fetching data from the API: {e}"})

    return render(request, 'Apps/nearby.html')


#ats
#Y1VHS1k1VW1NandXeXBaMmFIT3FNZz09
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Your Recruitee API URL (replace with correct URL from documentation)
RECRUITE_API_URL = "https://api.recruitee.com/v1/candidates"
API_KEY = "Y1VHS1k1VW1NandXeXBaMmFIT3FNZz09"  # Replace with your actual API key

@csrf_exempt
def ats(request):
    if request.method == "POST":
        # Get the uploaded resume file
        file = request.FILES.get('resume')
        if not file:
            return JsonResponse({'error': 'No resume uploaded'}, status=400)

        # Prepare the data for the API request
        files = {'file': file}
        headers = {
    'Authorization': f'Bearer {API_KEY}',
}
        # Make the API call to Recruitee's ATS service
        try:
            response = requests.post(RECRUITE_API_URL, files=files, headers=headers)

            if response.status_code == 200:
                ats_data = response.json()
                ats_score = ats_data.get("score", 0)  # Modify based on actual response structure
                return JsonResponse({'ats_score': ats_score})
            else:
                return JsonResponse({
                    'error': 'Error fetching ATS score',
                    'details': response.json()  # Provide the exact response from the API for debugging
                }, status=response.status_code)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': 'API request failed', 'details': str(e)}, status=500)

    else:
        # GET request to show the upload form
        return render(request, 'Apps/upload.html')


#url Shortner


url_mapping = {}

# Use settings for base URL (it can be dynamically set in production)
BASE_URL = settings.BASE_URL if hasattr(settings, 'BASE_URL') else '127.0.0.1:8000/'

def shorten_url(request):
    if request.method == 'POST':
        original_url = request.POST.get('original_url')
        custom_name = request.POST.get('custom_name')

        if original_url:
            # Use custom name if provided; otherwise, generate a random short code
            short_code = custom_name if custom_name else get_random_string(length=6)

            if short_code in url_mapping:
                return render(request, 'Apps/shortener.html', {'error': 'This name is already taken!'})

            # Map the short code to the original URL
            url_mapping[short_code] = original_url

            # Generate the shortened URL
            short_url = f"{BASE_URL}{short_code}"
            return render(request, 'Apps/shortener.html', {'short_url': short_url})
    return render(request, 'Apps/shortener.html')

def redirect_url(request, short_code):
    original_url = url_mapping.get(short_code)
    if original_url:
        return HttpResponseRedirect(original_url)
    else:
        return render(request, 'Apps/shortener.html', {'error': 'Invalid short URL'})



#human

# from django.shortcuts import render
# from django.http import JsonResponse
# from transformers import pipeline

# # Initialize the Hugging Face model pipeline
# humanizer = pipeline("text-generation", model="gpt2")

# def humanize_text(request):
#     if request.method == 'POST':
#         input_text = request.POST.get('input_text')  # Get input from the form
        
#         if input_text:
#             # Generate humanized text using GPT2 or any other suitable model
#             result = humanizer(input_text, max_length=150, num_return_sequences=1)

#             # Extract the generated text
#             humanized_text = result[0]['generated_text']
#             return render(request, 'Apps/humanizer.html', {'original_text': input_text, 'humanized_text': humanized_text})
        
#     return render(request, 'Apps/humanizer.html')

# from django.shortcuts import render
# from django.http import JsonResponse
# from transformers import pipeline
# import nltk
# from nltk.corpus import wordnet
# import random

# # Ensure NLTK data is downloaded
# nltk.download('wordnet')
# nltk.download('omw-1.4')

# # Initialize the Hugging Face model pipeline for text generation
# humanize_pipeline = pipeline("text2text-generation", model="EleutherAI/gpt-neo-125M")

# # Function to simplify and dynamically replace words with synonyms
# def dynamic_word_replacement(text):
#     """
#     This function dynamically replaces words with their synonyms to make the text more variable.
#     """
#     words = text.split()
#     new_words = []
    
#     for word in words:
#         # Get synonyms for each word
#         synonyms = wordnet.synsets(word)
#         if synonyms:
#             # Get the first synonym's lemma (root form of the word)
#             synonym = synonyms[0].lemmas()[0].name()
#             # Add the synonym if it is different from the original word
#             if synonym.lower() != word.lower():
#                 new_words.append(synonym)
#             else:
#                 new_words.append(word)
#         else:
#             new_words.append(word)

#     # Join words back into a sentence
#     return " ".join(new_words)

# # Function to refine AI-generated text
# def refine_text(ai_generated_text):
#     """
#     Function to simplify and shorten AI-generated text to under 300 characters.
#     """
#     # Basic cleanup
#     refined_text = ai_generated_text.strip()

#     # Dynamically replace words with synonyms
#     humanized_text = dynamic_word_replacement(refined_text)

#     # Limit the text to 300 characters
#     humanized_text = humanized_text[:300]

#     # Add a human-like closing (optional)
#     humanized_text += " Thank you! 😊"

#     return humanized_text

# def humanize_text(request):
#     """
#     View function to handle the humanization of AI-generated text.
#     This will accept text from a POST request, process it, and return refined text.
#     """
#     if request.method == 'POST':
#         input_text = request.POST.get('input_text')  # Get input from the form

#         if input_text:
#             # Generate text using GPT2 (you can also use a larger model here for better quality)
#             result = humanizer(input_text, max_length=300, num_return_sequences=1)

#             # Extract the generated text from GPT2 output
#             ai_generated_text = result[0]['generated_text']

#             # Refine the text to make it simpler and under 300 characters with dynamic words
#             humanized_text = refine_text(ai_generated_text)

#             # Render the response with original and humanized text
#             return render(request, 'Apps/humanizer.html', {
#                 'original_text': input_text,
#                 'humanized_text': humanized_text
#             })

#     return render(request, 'Apps/humanizer.html')
# from django.shortcuts import render
# from django.http import JsonResponse
# from transformers import pipeline

# # Initialize the Hugging Face model pipeline for text generation using GPT-Neo
# humanize_pipeline = pipeline("text-generation", model="EleutherAI/gpt-neo-1.3B")

# def refine_text(ai_generated_text):
#     """
#     Function to refine AI-generated text by cleaning it up and making it more human-like.
#     """
#     # Basic cleanup and trimming
#     refined_text = ai_generated_text.strip()

#     # Limit the text length for brevity (e.g., to 300 characters)
#     refined_text = refined_text[:300]

#     return refined_text

# def humanize_text(request):
#     """
#     View to handle converting AI-generated text into a human-like format.
#     """
#     if request.method == 'POST':
#         input_text = request.POST.get('input_text')

#         if input_text:
#             try:
#                 # Generate text using GPT-Neo model
#                 result = humanize_pipeline(f"Make this text more human-like: {input_text}", max_length=200)

#                 # Extract AI-generated text
#                 ai_generated_text = result[0]['generated_text']

#                 # Refine the generated text to make it more natural
#                 humanized_text = refine_text(ai_generated_text)

#                 # Return both original and humanized text to the template
#                 return render(request, 'Apps/humanizer.html', {
#                     'original_text': input_text,
#                     'humanized_text': humanized_text
#                 })
#             except Exception as e:
#                 return JsonResponse({"error": str(e)}, status=500)

#     return render(request, 'Apps/humanizer.html')
