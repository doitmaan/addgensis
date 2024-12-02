from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from openai import OpenAI
from google_images_search import GoogleImagesSearch
from .models import Advertisement
from .serializer import AdvertisementSerializer
import os

class GenerateAdvertView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            ad_description = request.data.get('ad_description')
            img_description = request.data.get('img_description')
            image_file = request.FILES.get('image')
            
            if not ad_description or not img_description:
                return Response(
                    {'error': 'Missing description'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate content using OpenAI
            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """
                        You are an expert copywriter specializing in creating compelling advertisements for second-hand goods.
                        Your task is to craft engaging, honest, and persuasive adverts that highlight the unique value of pre-owned items.
                        Follow these guidelines:
                        1. Tone: Maintain a friendly, enthusiastic, and trustworthy tone.
                        2. Structure: Use a catchy headline, followed by 2-3 short paragraphs, and end with a call-to-action.
                        3. Content:
                        - Highlight the item's best features and any unique selling points.
                        - Mention the item's condition honestly but positively.
                        - Include any relevant history or interesting facts about the item.
                        - If applicable, compare the second-hand price to the new item price.
                        4. Language: Use vivid, descriptive language to help the reader visualize the item.
                        5. Call-to-Action: Encourage potential buyers to act quickly, emphasizing the unique opportunity.
                        Avoid:
                        - Exaggeration or false claims
                        - Negative language about the item's age or condition
                        - Overly complex or technical jargon
                        Aim for an advert length of 100-150 words unless specified otherwise.
                    """},
                    {"role": "user", "content": f"Generate an advert for the given description. The description is: {ad_description}."}
                ]
            )

            # Search for images if no image was uploaded
            if not image_file:
                self.image_search(img_description)

            # Save to database
            advertisement = Advertisement.objects.create(
                description=ad_description,
                image_description=img_description,
                generated_content=completion.choices[0].message.content,
                image=image_file if image_file else None
            )

            serializer = AdvertisementSerializer(advertisement)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def image_search(self, description):
        api_key = os.environ.get('GOOGLE_API_KEY')
        cx = os.environ.get('GOOGLE_CX')
        path = os.environ.get('IMAGES_PATH')
        
        gis = GoogleImagesSearch(api_key, cx)
        search_params = {
            'q': description,
            'num': 2,
            'imgSize': 'medium',
            'imgColorType': 'color'
        }
        
        gis.search(
            search_params=search_params,
            path_to_dir=path
        )
        return gis.results()

# settings.py (add these settings)
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')