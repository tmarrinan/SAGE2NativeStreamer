import platform
from PIL import Image

operatingSystem = platform.system()

if operatingSystem == "Darwin":
    import Quartz.CoreGraphics as CG

def screenshot(region=None, window=None):
    if operatingSystem == "Windows":
        return screenshotWindows(region, window)
    elif operatingSystem == "Darwin":
        return screenshotMacOSX(region, window)
    else:
        return screenshotLinux(region, window)

def screenshotMacOSX(region, window):
    rect = None
    image = None
    
    if window != None:
        windowInfo = CG.CGWindowListCopyWindowInfo(CG.kCGWindowListOptionIncludingWindow, window)
        windowRegion = windowInfo[0]["kCGWindowBounds"]
        rect = CG.CGRectMake(windowRegion["X"], windowRegion["Y"], int(16 * round(float(windowRegion["Width"])/16)), windowRegion["Height"])
        image = CG.CGWindowListCreateImage(
            rect,
            CG.kCGWindowListOptionIncludingWindow,
            window,
            CG.kCGWindowImageBoundsIgnoreFraming)
    else:
        if region != None:
            rect = CG.CGRectMake(region[0], region[1], int(16 * round(float(region[2])/16)), region[3])
        else:
            rect = CG.CGRectInfinite
        image = CG.CGWindowListCreateImage(
            rect,
            CG.kCGWindowListOptionOnScreenOnly,
            CG.kCGNullWindowID,
            CG.kCGWindowImageDefault)

    bpp = CG.CGImageGetBitsPerPixel(image)
    info = CG.CGImageGetBitmapInfo(image)
    pixeldata = CG.CGDataProviderCopyData(CG.CGImageGetDataProvider(image))

    pImg = None
    colorspace = "RGBA"
    if bpp == 32:
        alphaInfo = info & CG.kCGBitmapAlphaInfoMask
        # BGRA
        if alphaInfo == CG.kCGImageAlphaPremultipliedFirst or alphaInfo == CG.kCGImageAlphaFirst or alphaInfo == CG.kCGImageAlphaNoneSkipFirst:
            pImg = Image.fromstring("RGBA", (CG.CGImageGetWidth(image), CG.CGImageGetHeight(image)), pixeldata, "raw", "BGRA")
        # RGBA
        else:
            pImg = Image.fromstring("RGBA", (CG.CGImageGetWidth(image), CG.CGImageGetHeight(image)), pixeldata)
    elif bpp == 24:
        # RGB
        pImg = Image.fromstring("RGB", (CG.CGImageGetWidth(image), CG.CGImageGetHeight(image)), pixeldata)

    return pImg
