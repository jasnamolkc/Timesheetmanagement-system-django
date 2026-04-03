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
# from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

# def create_video_poster(poster, width, height, output_name):

#     video = VideoFileClip(poster.content_video.path).resize((width, height))

#     # Logo overlay
#     logo = (ImageClip(poster.logo.path)
#             .set_duration(video.duration)
#             .resize(height=height * 0.15)
#             .set_position(("right", "bottom")))

#     final = CompositeVideoClip([video, logo])

#     output_path = os.path.join(settings.MEDIA_ROOT, f"videos/{output_name}.mp4")
#     final.write_videofile(output_path, fps=24)

#     return output_path
import cv2
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image

def generate_video_thumbnail(poster):
    if not poster.content_video:
        return

    video_path = poster.content_video.path

    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    cap.release()

    if success:
        # Convert BGR → RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        img = Image.fromarray(frame)

        buffer = BytesIO()
        img.save(buffer, format='JPEG')

        poster.video_thumbnail.save(
            f"thumb_{poster.id}.jpg",
            ContentFile(buffer.getvalue()),
            save=False
        )
import cv2
import numpy as np
from PIL import Image
import os
from django.conf import settings


def overlay_logo(frame, logo_np, x, y):
    h, w = logo_np.shape[:2]

    for c in range(0, 3):
        frame[y:y+h, x:x+w, c] = (
            logo_np[:, :, c] * (logo_np[:, :, 3] / 255.0) +
            frame[y:y+h, x:x+w, c] * (1.0 - logo_np[:, :, 3] / 255.0)
        )

    return frame


def generate_video_with_logo(poster, width, height, filename):
    video_path = poster.content_video.path
    logo_path = poster.logo.path

    # Load logo
    logo = Image.open(logo_path).convert("RGBA")

    # Resize logo (bigger & visible)
    logo_width = int(width * 0.25)
    logo_height = int(logo.height * (logo_width / logo.width))
    logo = logo.resize((logo_width, logo_height))

    logo_np = np.array(logo)

    cap = cv2.VideoCapture(video_path)

    # Output path
    output_path = os.path.join(settings.MEDIA_ROOT, f"videos/{filename}.mp4")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 24, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize video frame
        frame = cv2.resize(frame, (width, height))

        # Position logo (bottom-right)
        x = width - logo_width - 20
        y = height - logo_height - 20

        frame = overlay_logo(frame, logo_np, x, y)

        # Add title
        cv2.putText(
            frame,
            poster.title,
            (50, height - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2
        )

        out.write(frame)

    cap.release()
    out.release()

    return output_path
def generate_video_posters(poster):
    from django.conf import settings

    if not poster.content_video:
        return

    insta = generate_video_with_logo(poster, 1080, 1080, f"insta_{poster.id}")
    whatsapp = generate_video_with_logo(poster, 800, 800, f"whatsapp_{poster.id}")
    facebook = generate_video_with_logo(poster, 1200, 630, f"facebook_{poster.id}")

    poster.video_instagram = insta.replace(settings.MEDIA_ROOT + "/", "")
    poster.video_whatsapp = whatsapp.replace(settings.MEDIA_ROOT + "/", "")
    poster.video_facebook = facebook.replace(settings.MEDIA_ROOT + "/", "")

    poster.save()