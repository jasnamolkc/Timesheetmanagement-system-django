from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.conf import settings
import os
from io import BytesIO


def create_canvas(width, height, poster):
    img = Image.new('RGB', (width, height), 'white')

    logo = Image.open(poster.logo.path).convert("RGBA")
    content = Image.open(poster.content_image.path).convert("RGBA")

    logo = logo.resize((int(width * 0.2), int(height * 0.2)))
    content = content.resize((int(width * 0.8), int(height * 0.5)))

    img.paste(content, (int(width*0.1), int(height*0.25)), content)
    img.paste(logo, (20, 20), logo)

    draw = ImageDraw.Draw(img)

    try:
        font_path = os.path.join(settings.BASE_DIR, 'fonts/Poppins-Regular.ttf')
        font = ImageFont.truetype(font_path, int(width * 0.05))
    except:
        font = ImageFont.load_default()
    draw.text((50, int(height*0.85)), poster.title, fill="black", font=font)

    return img


def save_image(img, field, filename):
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    file = ContentFile(buffer.getvalue())
    field.save(filename, file, save=False)


def generate_all_posters(poster):
    insta = create_canvas(1080, 1080, poster)
    whatsapp = create_canvas(800, 800, poster)
    facebook = create_canvas(1200, 630, poster)

    save_image(insta, poster.instagram_image, f"insta_{poster.id}.jpg")
    save_image(whatsapp, poster.whatsapp_image, f"whatsapp_{poster.id}.jpg")
    save_image(facebook, poster.facebook_image, f"facebook_{poster.id}.jpg")

    poster.save()