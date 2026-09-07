"""
Creates a synthetic 2D floor-plan raster (simulating a CAD/PDF export) for the
QTO computer-vision demo. Draws a simple G+2-style ground floor unit layout
with room partitions, a scale bar, and door/window gap markers.
Output: sample_floor_plan.png  (also copied to app/assets/)
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1400, 1000
PX_PER_M = 60  # scale: 60 pixels = 1 metre (this is the "known" ground truth used for QA)

img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

WALL = (20, 20, 20)
WALL_TH = 6

def rect(x1, y1, x2, y2, th=WALL_TH, color=WALL):
    d.rectangle([x1, y1, x2, y2], outline=color, width=th)

def line(x1, y1, x2, y2, th=WALL_TH, color=WALL):
    d.line([x1, y1, x2, y2], fill=color, width=th)

ox, oy = 100, 100  # outer plan origin
# Outer boundary: 18m x 12m plot -> building footprint 15m x 10m (in px)
bw, bh = int(15 * PX_PER_M), int(10 * PX_PER_M)
rect(ox, oy, ox + bw, oy + bh)

# Internal partitions forming rooms (approx, illustrative layout)
# Living room / hall
line(ox + int(6*PX_PER_M), oy, ox + int(6*PX_PER_M), oy + int(6*PX_PER_M))
# Bedroom 1 partition
line(ox + int(6*PX_PER_M), oy + int(6*PX_PER_M), ox + bw, oy + int(6*PX_PER_M))
# Bedroom 2 partition
line(ox + int(10*PX_PER_M), oy, ox + int(10*PX_PER_M), oy + int(6*PX_PER_M))
# Kitchen partition
line(ox, oy + int(6*PX_PER_M), ox + int(6*PX_PER_M), oy + int(6*PX_PER_M))
line(ox + int(3*PX_PER_M), oy + int(6*PX_PER_M), ox + int(3*PX_PER_M), oy + bh)
# Toilet partition
line(ox + int(10*PX_PER_M), oy + int(3*PX_PER_M), ox + bw, oy + int(3*PX_PER_M))

# Door gap markers (small white breaks in walls to simulate openings)
def door_gap(x1, y1, x2, y2, width=18):
    d.line([x1, y1, x2, y2], fill="white", width=width)

door_gap(ox + int(6*PX_PER_M), oy + int(3*PX_PER_M) - 30, ox + int(6*PX_PER_M), oy + int(3*PX_PER_M) + 30)
door_gap(ox + int(1.2*PX_PER_M), oy + int(6*PX_PER_M) - 30, ox + int(1.2*PX_PER_M), oy + int(6*PX_PER_M) + 30)

# Labels
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    font_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except Exception:
    font = ImageFont.load_default()
    font_s = font

labels = [
    ("LIVING / HALL", ox + int(2.5*PX_PER_M), oy + int(2.5*PX_PER_M)),
    ("BEDROOM 1", ox + int(7.5*PX_PER_M), oy + int(2.5*PX_PER_M)),
    ("BEDROOM 2", ox + int(11.5*PX_PER_M), oy + int(4*PX_PER_M)),
    ("TOILET", ox + int(11.5*PX_PER_M), oy + int(1.2*PX_PER_M)),
    ("KITCHEN", ox + int(1.2*PX_PER_M), oy + int(7.5*PX_PER_M)),
    ("DINING", ox + int(4*PX_PER_M), oy + int(8*PX_PER_M)),
]
for text, x, y in labels:
    d.text((x, y), text, fill=(60, 60, 60), font=font_s)

d.text((ox, oy - 40), "GROUND FLOOR PLAN - THAMEAHWARAN RESIDENCY (Not to scale copy - CAD export)", fill=WALL, font=font)

# Scale bar: 1 metre reference
sb_x, sb_y = ox, oy + bh + 60
d.line([sb_x, sb_y, sb_x + PX_PER_M, sb_y], fill=WALL, width=4)
d.line([sb_x, sb_y - 8, sb_x, sb_y + 8], fill=WALL, width=3)
d.line([sb_x + PX_PER_M, sb_y - 8, sb_x + PX_PER_M, sb_y + 8], fill=WALL, width=3)
d.text((sb_x, sb_y + 12), "1.0 m scale reference", fill=WALL, font=font_s)

os.makedirs("../assets", exist_ok=True)
img.save("sample_floor_plan.png")
img.save("../assets/sample_floor_plan.png")
print("Saved sample_floor_plan.png", img.size)
