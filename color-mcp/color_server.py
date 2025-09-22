
import random
import colorsys
import os
from fastmcp import FastMCP

mcp = FastMCP("ColorTools")

@mcp.tool()
def hex_to_rgb(hex_color: str) -> str:
    """Convert HEX color to RGB values"""
    try:
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Validate hex color
        if len(hex_color) != 6:
            return "Error: HEX color must be 6 characters long (e.g., #FF0000 or FF0000)"
        
        # Convert to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        return f"HEX #{hex_color.upper()} = RGB({rgb[0]}, {rgb[1]}, {rgb[2]})"
    
    except ValueError:
        return "Error: Invalid HEX color format. Use format like #FF0000 or FF0000"

@mcp.tool()
def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to HEX color"""
    try:
        # Validate RGB values
        if not all(0 <= val <= 255 for val in [r, g, b]):
            return "Error: RGB values must be between 0 and 255"
        
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        
        return f"RGB({r}, {g}, {b}) = HEX {hex_color}"
    
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def random_color() -> str:
    """Generate a random color in both HEX and RGB formats"""
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    
    hex_color = f"#{r:02X}{g:02X}{b:02X}"
    
    return f"Random Color: HEX {hex_color} | RGB({r}, {g}, {b})"

@mcp.tool()
def color_palette(base_color: str, palette_type: str = "complementary") -> str:
    """Generate color palette based on a base color"""
    try:
        # Parse base color (assuming HEX)
        base_color = base_color.lstrip('#')
        if len(base_color) != 6:
            return "Error: Base color must be in HEX format (e.g., #FF0000)"
        
        # Convert to RGB then HSV
        rgb = tuple(int(base_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = [x/255.0 for x in rgb]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        colors = [f"#{base_color.upper()} (base)"]
        
        if palette_type == "complementary":
            # Complementary color (opposite on color wheel)
            comp_h = (h + 0.5) % 1.0
            comp_rgb = colorsys.hsv_to_rgb(comp_h, s, v)
            comp_rgb = tuple(int(x * 255) for x in comp_rgb)
            colors.append(f"#{comp_rgb[0]:02X}{comp_rgb[1]:02X}{comp_rgb[2]:02X} (complementary)")
            
        elif palette_type == "triadic":
            for offset in [1/3, 2/3]:
                tri_h = (h + offset) % 1.0
                tri_rgb = colorsys.hsv_to_rgb(tri_h, s, v)
                tri_rgb = tuple(int(x * 255) for x in tri_rgb)
                colors.append(f"#{tri_rgb[0]:02X}{tri_rgb[1]:02X}{tri_rgb[2]:02X} (triadic)")
                
        elif palette_type == "analogous":
            for offset in [-30/360, 30/360]:
                ana_h = (h + offset) % 1.0
                ana_rgb = colorsys.hsv_to_rgb(ana_h, s, v)
                ana_rgb = tuple(int(x * 255) for x in ana_rgb)
                colors.append(f"#{ana_rgb[0]:02X}{ana_rgb[1]:02X}{ana_rgb[2]:02X} (analogous)")
        
        return f"{palette_type.capitalize()} Palette:\n" + "\n".join(colors)
    
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def color_contrast(color1: str, color2: str) -> str:
    """Calculate contrast ratio between two colors"""
    try:
        def hex_to_luminance(hex_color):
            hex_color = hex_color.lstrip('#')
            rgb = [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
            
            # Convert to linear RGB
            rgb = [x/12.92 if x <= 0.03928 else ((x + 0.055)/1.055)**2.4 for x in rgb]
            
            # Calculate luminance
            return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        
        lum1 = hex_to_luminance(color1)
        lum2 = hex_to_luminance(color2)
        
        # Calculate contrast ratio
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        contrast = (lighter + 0.05) / (darker + 0.05)
        
        # Determine accessibility level
        if contrast >= 7:
            level = "AAA (excellent)"
        elif contrast >= 4.5:
            level = "AA (good)"
        elif contrast >= 3:
            level = "AA Large Text (acceptable)"
        else:
            level = "Failed (poor contrast)"
        
        return f"Contrast between {color1.upper()} and {color2.upper()}:\nRatio: {contrast:.2f}:1\nAccessibility: {level}"
    
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def color_info(hex_color: str) -> str:
    """Get detailed information about a color"""
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return "Error: Color must be in HEX format (e.g., #FF0000)"
        
        # Convert to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = [x/255.0 for x in rgb]
        
        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        # Convert to HSL
        h_hsl, l, s_hsl = colorsys.rgb_to_hls(r, g, b)
        
        # Determine color family
        hue_deg = h * 360
        if hue_deg < 15 or hue_deg >= 345:
            color_family = "Red"
        elif hue_deg < 45:
            color_family = "Orange"
        elif hue_deg < 75:
            color_family = "Yellow"
        elif hue_deg < 165:
            color_family = "Green"
        elif hue_deg < 255:
            color_family = "Blue"
        elif hue_deg < 285:
            color_family = "Purple"
        else:
            color_family = "Pink"
        
        return f"""Color Information for #{hex_color.upper()}:
RGB: ({rgb[0]}, {rgb[1]}, {rgb[2]})
HSV: ({hue_deg:.0f}°, {s*100:.0f}%, {v*100:.0f}%)
HSL: ({h_hsl*360:.0f}°, {s_hsl*100:.0f}%, {l*100:.0f}%)
Color Family: {color_family}
Brightness: {(0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2]):.0f}/255"""
    
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def color_mixer(color1: str, color2: str, ratio: float = 0.5) -> str:
    """Mix two colors together with specified ratio"""
    try:
        if not 0 <= ratio <= 1:
            return "Error: Ratio must be between 0 and 1 (0 = 100% color1, 1 = 100% color2)"
        
        # Parse colors
        color1 = color1.lstrip('#')
        color2 = color2.lstrip('#')
        
        if len(color1) != 6 or len(color2) != 6:
            return "Error: Both colors must be in HEX format (e.g., #FF0000)"
        
        # Convert to RGB
        rgb1 = tuple(int(color1[i:i+2], 16) for i in (0, 2, 4))
        rgb2 = tuple(int(color2[i:i+2], 16) for i in (0, 2, 4))
        
        # Mix colors
        mixed_rgb = tuple(int(rgb1[i] * (1 - ratio) + rgb2[i] * ratio) for i in range(3))
        mixed_hex = f"#{mixed_rgb[0]:02X}{mixed_rgb[1]:02X}{mixed_rgb[2]:02X}"
        
        percentage1 = int((1 - ratio) * 100)
        percentage2 = int(ratio * 100)
        
        return f"Mixed Color: #{color1.upper()} ({percentage1}%) + #{color2.upper()} ({percentage2}%) = {mixed_hex}"
    
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if os.getenv("RENDER"):
        mcp.run()
    else:
        mcp.run()