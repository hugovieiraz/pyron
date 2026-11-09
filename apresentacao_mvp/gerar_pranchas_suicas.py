import numpy as np
from PIL import Image, ImageDraw, ImageFont

ART = r"C:\Users\gabri\.gemini\antigravity\brain\e134b1db-cabe-4904-a703-b88fa9900654"
BG_HEX = (246, 245, 240)  # Exact warm architectural paper #F6F5F0

def create_swiss_base(width=1920, height=1080):
    img = Image.new("RGB", (width, height), BG_HEX)
    draw = ImageDraw.Draw(img)

    # Outer frame border at 36px margin
    m = 36
    border_col = (195, 192, 184)
    tick_col = (180, 177, 168)
    cross_col = (186, 183, 175)

    draw.rectangle([m, m, width - m, height - m], outline=border_col, width=2)

    # Millimeter ticks along all 4 outer edges
    for x in range(m, width - m + 1, 8):
        h_tick = 18 if (x - m) % 80 == 0 else (12 if (x - m) % 40 == 0 else 7)
        draw.line([(x, m - h_tick), (x, m)], fill=tick_col, width=1)
        draw.line([(x, height - m), (x, height - m + h_tick)], fill=tick_col, width=1)

    for y in range(m, height - m + 1, 8):
        w_tick = 18 if (y - m) % 80 == 0 else (12 if (y - m) % 40 == 0 else 7)
        draw.line([(m - w_tick, y), (m, y)], fill=tick_col, width=1)
        draw.line([(width - m, y), (width - m + w_tick, y)], fill=tick_col, width=1)

    # Swiss registration '+' crosshairs across the canvas
    xs = [68, 244, 496, 748, 996, 1248, 1500, 1752, 1852]
    ys = [68, 294, 524, 754, 1012]
    for cx in xs:
        for cy in ys:
            draw.line([(cx - 9, cy), (cx + 9, cy)], fill=cross_col, width=1)
            draw.line([(cx, cy - 9), (cx, cy + 9)], fill=cross_col, width=1)

    return img, draw

def blend_figure_onto_swiss(base_img, fig_path, dst_box, crop_box=None, tint_white=True):
    """
    Loads a Nano Banana scientific figure, crops if requested, maps pure white (#FFFFFF)
    to warm Swiss off-white (#F6F5F0) so it blends seamlessly into the drafting paper,
    adds a crisp 1px CAD border and corner ticks, and pastes at dst_box = (x1, y1, x2, y2).
    """
    fig = Image.open(fig_path).convert("RGB")
    if crop_box is not None:
        w, h = fig.size
        c = (
            int(crop_box[0] * w),
            int(crop_box[1] * h),
            int(crop_box[2] * w),
            int(crop_box[3] * h)
        )
        fig = fig.crop(c)

    target_w = dst_box[2] - dst_box[0]
    target_h = dst_box[3] - dst_box[1]
    fig = fig.resize((target_w, target_h), Image.Resampling.LANCZOS)

    arr = np.array(fig, dtype=np.float32)
    if tint_white:
        # Multiply near-white pixels by (246/255, 245/255, 240/255) so white background matches #F6F5F0 seamlessly
        lum = arr.mean(axis=2)
        # Smooth mask for bright background pixels (lum > 225)
        alpha = np.clip((lum - 215.0) / 35.0, 0.0, 1.0)[..., None]
        tinted = arr * np.array([246.0 / 255.0, 245.0 / 255.0, 240.0 / 255.0], dtype=np.float32)
        arr = arr * (1.0 - alpha) + tinted * alpha

    out_fig = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    base_img.paste(out_fig, (dst_box[0], dst_box[1]))

    draw = ImageDraw.Draw(base_img)
    x1, y1, x2, y2 = dst_box
    # Crisp Swiss CAD frame around the technical figure zone
    draw.rectangle([x1, y1, x2, y2], outline=(185, 182, 174), width=2)
    # Corner L-brackets in dark ink
    L = 14
    ink = (30, 41, 59)
    for (cx, cy, dx, dy) in [(x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)]:
        draw.line([(cx, cy), (cx + dx * L, cy)], fill=ink, width=3)
        draw.line([(cx, cy), (cx, cy + dy * L)], fill=ink, width=3)

# 1. Slide 2: Joule Load Illusion (fig_slide2_joule_load_illusion_1794084638035.jpg)
img2, _ = create_swiss_base()
blend_figure_onto_swiss(
    img2,
    f"{ART}\\fig_slide2_joule_load_illusion_1794084638035.jpg",
    dst_box=(760, 120, 1845, 920),
    crop_box=(0.0, 0.0, 1.0, 1.0)
)
img2.save(f"{ART}\\swiss_board_slide2.jpg", quality=95)

# 2. Slide 3: Joule Constriction vs Arrhenius (fig_slide3_joule_vs_arrhenius_1794084644485.jpg)
img3, draw3 = create_swiss_base()
blend_figure_onto_swiss(
    img3,
    f"{ART}\\fig_slide3_joule_vs_arrhenius_1794084644485.jpg",
    dst_box=(760, 120, 1845, 920),
    crop_box=(0.0, 0.0, 1.0, 1.0)
)
img3.save(f"{ART}\\swiss_board_slide3.jpg", quality=95)

# 3. Slide 4: ZnO Surge Arrester Cutaway (fig_slide4_zno_arrester_cutaway_1794084621144.jpg)
img4, _ = create_swiss_base()
blend_figure_onto_swiss(
    img4,
    f"{ART}\\fig_slide4_zno_arrester_cutaway_1794084621144.jpg",
    dst_box=(760, 120, 1845, 920),
    crop_box=(0.0, 0.0, 1.0, 1.0)
)
img4.save(f"{ART}\\swiss_board_slide4.jpg", quality=95)

# 4. Slide 5: Three-Phase Comparative Thermography & NBR 15866 Matrix (fig_slide5_nbr15866_phases_1794084630299.jpg)
img5, _ = create_swiss_base()
blend_figure_onto_swiss(
    img5,
    f"{ART}\\fig_slide5_nbr15866_phases_1794084630299.jpg",
    dst_box=(760, 120, 1845, 920),
    crop_box=(0.0, 0.14, 1.0, 1.0)
)
img5.save(f"{ART}\\swiss_board_slide5.jpg", quality=95)

print("Generated swiss_board_slide2..5.jpg successfully!")
