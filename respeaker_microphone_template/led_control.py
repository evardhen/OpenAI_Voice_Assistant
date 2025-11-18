from usb_pixel_ring_v2 import PixelRing
import usb.core
import usb.util
import sys

def initialize_pixel_ring():
    dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
    if dev:
        pixel_ring = PixelRing(dev)
        pixel_ring.off()
    else:
        pixel_ring = None
    return pixel_ring

def set_mono_color(color):
    pixel_ring = initialize_pixel_ring()
    pixel_ring.mono(color)

def set_color_palette():
    pixel_ring = initialize_pixel_ring()
    pixel_ring.set_color_palette(0x2a57de, 0xde902a)

def activate_doa():
    pixel_ring = initialize_pixel_ring()
    pixel_ring.set_color_palette(0x21bf13, 0x060acf)
    pixel_ring.listen()
    #pixel_ring.trace()

def speak_mode():
    pixel_ring = initialize_pixel_ring()
    pixel_ring.set_color_palette(0x210f4d, 0x5f0a70)
    pixel_ring.speak()

def wait_mode():
    pixel_ring = initialize_pixel_ring()
    pixel_ring.think()

def set_brightness(brightness):
    if 0x00 <= brightness <= 0x1F:
        pixel_ring = initialize_pixel_ring()
        pixel_ring.set_brightness(brightness)
    else:
        print("Error: Brightness value out of range (0x00 to 0x1F)")

def turn_off():
    pixel_ring = initialize_pixel_ring()
    pixel_ring.off()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "initialize_pixel_ring":
        initialize_pixel_ring()
    elif len(sys.argv) > 1 and sys.argv[1] == "set_mono_color":
        set_mono_color()
    elif len(sys.argv) > 1 and sys.argv[1] == "activate_doa":
        activate_doa()
    elif len(sys.argv) > 1 and sys.argv[1] == "speak_mode":
        speak_mode()
    elif len(sys.argv) > 1 and sys.argv[1] == "wait_mode":
        wait_mode()
    elif len(sys.argv) > 1 and sys.argv[1] == "set_brightness":
        set_brightness()
    elif len(sys.argv) > 1 and sys.argv[1] == "turn_off":
        turn_off()
