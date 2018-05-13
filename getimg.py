from PIL import Image
import respath

def tray_icon():
    return Image.open(respath.resource_path("img/icon.ico"))