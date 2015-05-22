import platform
from PIL import Image

operatingSystem = platform.system()

if operatingSystem == "Windows":
    import win32gui
    import win32ui
    import win32con
elif operatingSystem == "Darwin":
    import Quartz.CoreGraphics as CG

def screenshot(region=None, window=None):
    if operatingSystem == "Windows":
        return screenshotWindows(region, window)
    elif operatingSystem == "Darwin":
        return screenshotMacOSX(region, window)
    else:
        return screenshotLinux(region, window)

def screenshotWindows(region, window):
    rect = None
    image = None
    
    if window != None:
        rect = list(win32gui.GetWindowRect(window))
        rect[2] = rect[2] - rect[0]
        rect[3] = rect[3] - rect[1]
        wDC = win32gui.GetWindowDC(window)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        image = win32ui.CreateBitmap()
        image.CreateCompatibleBitmap(dcObj, rect[2], rect[3])
        cDC.SelectObject(image)
        cDC.BitBlt((0,0),(rect[2], rect[3]) , dcObj, (0,0), win32con.SRCCOPY)
        
        imageInfo = image.GetInfo()
        bpp = imageInfo["bmBitsPixel"]
        pixeldata = image.GetBitmapBits(True)
        
        pImg = None
        if bpp == 32:
            pImg = Image.frombuffer("RGBA", (imageInfo["bmWidth"], imageInfo["bmHeight"]), pixeldata, "raw", "BGRA")
        elif bpp == 24:
            pImg = Image.frombuffer("RGB", (imageInfo["bmWidth"], imageInfo["bmHeight"]), pixeldata)
        
        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(window, wDC)
        win32gui.DeleteObject(image.GetHandle())
        
        return pImg

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
