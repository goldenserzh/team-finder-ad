import io
import random
import re
import uuid

from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from PIL import Image, ImageDraw, ImageFont

PHONE_RE = re.compile(r"^(\+7|8)(\d{10})$")

DEFAULT_PAGE_SIZE = 12
DEFAULT_PAGE_NUMBER = 1

AVATAR_SIZE = 200
AVATAR_FONT_SIZE = 110
AVATAR_RGB_MIN = 130
AVATAR_RGB_MAX = 210
AVATAR_DARK_THRESHOLD = 380
AVATAR_DARK_COLOR = (40, 40, 40)
AVATAR_LIGHT_COLOR = (250, 250, 250)
AVATAR_TEXT_VERTICAL_OFFSET = 4
AVATAR_FONT_FAMILY = "arial.ttf"


def _contrasting_color(bg):
    r, g, b = bg
    if r + g + b > AVATAR_DARK_THRESHOLD:
        return AVATAR_DARK_COLOR
    return AVATAR_LIGHT_COLOR


def generate_avatar_image_file(letter: str) -> ContentFile:
    letter = (letter or "?").strip()[:1].upper() or "?"
    bg = (
        random.randint(AVATAR_RGB_MIN, AVATAR_RGB_MAX),
        random.randint(AVATAR_RGB_MIN, AVATAR_RGB_MAX),
        random.randint(AVATAR_RGB_MIN, AVATAR_RGB_MAX),
    )
    img = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), bg)
    draw = ImageDraw.Draw(img)
    fill = _contrasting_color(bg)
    try:
        font = ImageFont.truetype(AVATAR_FONT_FAMILY, AVATAR_FONT_SIZE)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (
            (AVATAR_SIZE - tw) / 2,
            (AVATAR_SIZE - th) / 2 - AVATAR_TEXT_VERTICAL_OFFSET,
        ),
        letter,
        font=font,
        fill=fill,
    )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ContentFile(buf.read(), name=f"avatar_{uuid.uuid4().hex}.png")


def normalize_phone(value: str) -> str:
    value = (value or "").strip()
    m = PHONE_RE.match(value)
    if not m:
        return value
    return "+7" + m.group(2)


def paginate_queryset(request, qs, page_size=DEFAULT_PAGE_SIZE):
    paginator = Paginator(qs, page_size)
    page_number = request.GET.get("page") or DEFAULT_PAGE_NUMBER
    return paginator.get_page(page_number)


