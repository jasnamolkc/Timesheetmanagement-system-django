from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.conf import settings
import os
from io import BytesIO


# def create_canvas(width, height, poster):
#     img = Image.new('RGB', (width, height), 'white')

#     logo = Image.open(poster.logo.path).convert("RGBA")
#     content = Image.open(poster.content_image.path).convert("RGBA")

#     logo = logo.resize((int(width * 0.2), int(height * 0.2)))
#     content = content.resize((int(width * 0.8), int(height * 0.5)))

#     # img.paste(content, (int(width*0.1), int(height*0.25)), content)
#     # img.paste(logo, (20, 20), logo)
#     # Content position
#     content_x = int(width * 0.1)
#     content_y = int(height * 0.25)

#     img.paste(content, (content_x, content_y), content)

#     # ✅ Logo bottom-right ON CONTENT
#     logo_x = content_x + content.width - logo.width - 10
#     logo_y = content_y + content.height - logo.height - 10

#     img.paste(logo, (logo_x, logo_y), logo)

#     draw = ImageDraw.Draw(img)

#     try:
#         font_path = os.path.join(settings.BASE_DIR, 'fonts/Poppins-Regular.ttf')
#         font = ImageFont.truetype(font_path, int(width * 0.05))
#     except:
#         font = ImageFont.load_default()
#     # draw.text((50, int(height*0.85)), poster.title, fill="black", font=font)

#     return img

def create_canvas(width, height, poster):
    img = Image.new('RGB', (width, height), 'white')

    logo = Image.open(poster.logo.path).convert("RGBA")
    content = Image.open(poster.content_image.path).convert("RGBA")

    # 🔥 FULL COVER IMAGE
    content_ratio = content.width / content.height
    canvas_ratio = width / height

    if content_ratio > canvas_ratio:
        new_height = height
        new_width = int(new_height * content_ratio)
    else:
        new_width = width
        new_height = int(new_width / content_ratio)

    content = content.resize((new_width, new_height))

    left = (new_width - width) // 2
    top = (new_height - height) // 2
    content = content.crop((left, top, left + width, top + height))

    img.paste(content, (0, 0))

    # ✅ Logo bottom-right
    # logo = logo.resize((int(width * 0.15), int(height * 0.15)))
    # 🔥 Better logo scaling (keeps shape)
    logo_ratio = logo.width / logo.height

    logo_width = int(width * 0.25)
    logo_height = int(logo_width / logo_ratio)

    logo = logo.resize((logo_width, logo_height))


    logo_x = width - logo.width - 20
    logo_y = height - logo.height - 20

    img.paste(logo, (logo_x, logo_y), logo)

    # Title
    draw = ImageDraw.Draw(img)

    try:
        font_path = os.path.join(settings.BASE_DIR, 'fonts/Poppins-Regular.ttf')
        font = ImageFont.truetype(font_path, int(width * 0.05))
    except:
        font = ImageFont.load_default()

    draw.text((50, int(height * 0.85)), poster.title, fill="white", font=font)

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