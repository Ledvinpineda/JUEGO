import pygame
import pygame.freetype
import math

def render_text_gradient(font, text, rect, surface, gradient_colors, border_color, border_thickness):
    """
    Renders text with a gradient fill and an optional border.
    font: pygame.freetype.SysFont object
    text: string to render
    rect: pygame.Rect for positioning the text
    surface: pygame surface to draw on
    gradient_colors: list or tuple of two (R, G, B) colors for the gradient
    border_color: (R, G, B) color for the border
    border_thickness: integer for the border width
    """
    # Draw border first
    offsets = []
    for i in range(-border_thickness, border_thickness + 1):
        for j in range(-border_thickness, border_thickness + 1):
            if i != 0 or j != 0:
                offsets.append((i, j))
    
    for ox, oy in offsets:
        text_surf_border, text_rect_border = font.render(text, border_color)
        text_rect_border.center = (rect.centerx + ox, rect.centery + oy)
        surface.blit(text_surf_border, text_rect_border)  

    # Create a temporary surface for the gradient text
    text_size_for_gradient = font.get_rect(text).size  
    temp_surf_gradient = pygame.Surface(text_size_for_gradient, pygame.SRCALPHA)
    temp_surf_gradient_rect = temp_surf_gradient.get_rect()

    # Apply gradient to the temporary surface
    num_gradient_colors = len(gradient_colors)
    if num_gradient_colors < 2:
        # Fallback to solid color if not enough gradient colors are provided
        text_surf_main, text_rect_main = font.render(text, gradient_colors[0] if gradient_colors else (255,255,255))
        text_rect_main.center = rect.center
        surface.blit(text_surf_main, text_rect_main)
        return

    for y_pixel in range(temp_surf_gradient_rect.height):
        t = y_pixel / temp_surf_gradient_rect.height
        r = int(gradient_colors[0][0] * (1 - t) + gradient_colors[1][0] * t)
        g = int(gradient_colors[0][1] * (1 - t) + gradient_colors[1][1] * t)
        b = int(gradient_colors[0][2] * (1 - t) + gradient_colors[1][2] * t)
        current_color = (r, g, b)
        pygame.draw.line(temp_surf_gradient, current_color, (0, y_pixel), (temp_surf_gradient_rect.width, y_pixel))

    # Use the text as a mask to apply the gradient only to the text
    text_surf_mask, _ = font.render(text, (255, 255, 255)) # Render white text to use as mask
    temp_surf_gradient.blit(text_surf_mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
    
    # Blit the final gradient text to the main surface
    final_text_rect = temp_surf_gradient.get_rect(center=rect.center)
    surface.blit(temp_surf_gradient, final_text_rect)