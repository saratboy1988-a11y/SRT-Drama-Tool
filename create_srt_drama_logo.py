# save as: create_srt_drama_logo.py
from PIL import Image, ImageDraw, ImageFont
import math, os

def create_srt_drama_logo(size=512):
    # Create image with white background
    img: Image.Image = Image.new('RGBA', (size, size))
    # Fill with white background
    img.paste((255, 255, 255, 255), [0, 0, size, size])
    draw = ImageDraw.Draw(img)
    
    # Center point
    cx, cy = size // 2, size // 2
    
    # Create rounded square background with blue gradient
    for i in range(size):
        # Blue gradient (matching app theme)
        r = int(24 + (30 - 24) * i / size)
        g = int(144 + (140 - 144) * i / size)
        b = int(255 + (230 - 255) * i / size)
        
        # Draw horizontal lines for gradient
        draw.rectangle([(0, i), (size, i+1)], fill=(r, g, b, 255))
    
    # Create rounded corners mask
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    margin = size // 12
    mask_draw.rounded_rectangle([(margin, margin), (size-margin, size-margin)], 
                                 radius=size//10, fill=255)
    
    # Apply rounded corners
    img.putalpha(mask)
    
    # Redraw gradient on masked image
    draw = ImageDraw.Draw(img)
    for i in range(size):
        r = int(24 + (30 - 24) * i / size)
        g = int(144 + (140 - 144) * i / size)
        b = int(255 + (230 - 255) * i / size)
        draw.rectangle([(0, i), (size, i+1)], fill=(r, g, b, 255))
    
    # Apply mask again
    img.putalpha(mask)
    draw = ImageDraw.Draw(img)
    
    # Draw Play Button (center)
    play_size = size // 5
    play_points = [
        (cx - play_size//3, cy - play_size//2),  # Top left
        (cx - play_size//3, cy + play_size//2),  # Bottom left
        (cx + play_size//2, cy),  # Right center
    ]
    draw.polygon(play_points, fill=(255, 255, 255, 255))
    
    # Draw Audio Waves (around play button)
    wave_color = (255, 255, 255, 200)
    num_waves = 3
    
    for w in range(num_waves):
        wave_radius = size//4 + w * (size//16)
        alpha = 220 - w * 40
        
        # Left wave (curved)
        draw.arc(
            [(cx - wave_radius, cy - wave_radius//2), 
             (cx + wave_radius, cy + wave_radius//2)],
            start=100, end=260,
            fill=(255, 255, 255, alpha), width=5
        )
        
        # Right wave (curved)
        draw.arc(
            [(cx - wave_radius, cy - wave_radius//2), 
             (cx + wave_radius, cy + wave_radius//2)],
            start=-80, end=80,
            fill=(255, 255, 255, alpha), width=5
        )
    
    # Draw Subtitle Lines (bottom - representing SRT)
    line_width = size // 3
    line_gap = size // 40
    line_y_start = cy + size//4
    
    for i in range(3):
        line_y = line_y_start + i * line_gap
        line_len = line_width - i * (size//20)
        line_x = cx - line_len//2
        
        # Draw subtitle line
        draw.rounded_rectangle(
            [(line_x, line_y), (line_x + line_len, line_y + 6)],
            radius=3,
            fill=(255, 255, 255, 230)
        )
    
    # Add "SRT" text at top
    try:
        font = ImageFont.truetype("arialbd.ttf", size//12)
    except:
        font = ImageFont.load_default()
    
    text = "SRT"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = cx - text_width // 2
    text_y = size//8
    
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
    
    return img

# Create and save
if __name__ == "__main__":
    print("🎨 Creating SRT Drama Tool logo...")
    
    logo = create_srt_drama_logo(512)
    logo.save("srt_drama_tool.png", "PNG")
    print("✅ PNG saved: srt_drama_tool.png")
    
    # Create ICO with multiple sizes
    logo.save("logo.ico", format='ICO', sizes=[(16,16), (32,32), (48,48), (256,256)])
    print("✅ ICO saved: logo.ico")
    
    print("\n📝 To use in your app, add this to MainWindow.__init__():")
    print('''
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
    if os.path.exists(icon_path):
        self.setWindowIcon(QtGui.QIcon(icon_path))
    ''')
    
    print("\n✨ Logo created successfully!")
