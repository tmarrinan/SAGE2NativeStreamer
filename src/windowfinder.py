import platform

operatingSystem = platform.system()

if operatingSystem == "Windows":
    import win32gui
elif operatingSystem == "Darwin":
    import Quartz.CoreGraphics as CG

def findAllWindows():
    if operatingSystem == "Windows":
        return findAllWindowsWindows()
    elif operatingSystem == "Darwin":
        return findAllWindowsMacOSX()
    else:
        return findAllWindowsLinux()

def findAllWindowsWindows():
     validWindows = {}
     win32gui.EnumWindows(windowEnumerationHandler, validWindows)
     return validWindows
 
def findAllWindowsMacOSX():
    windowInfo = CG.CGWindowListCopyWindowInfo(CG.kCGWindowListOptionOnScreenOnly, CG.kCGNullWindowID)
    validWindows = {}

    for i in xrange(0, len(windowInfo)):
        if windowInfo[i]["kCGWindowLayer"] == 0:
            validWindows[windowInfo[i]["kCGWindowOwnerName"] + " - " + windowInfo[i]["kCGWindowName"]] = {
                "id":     windowInfo[i]["kCGWindowNumber"],
                "width":  windowInfo[i]["kCGWindowBounds"]["Width"],
                "height": windowInfo[i]["kCGWindowBounds"]["Height"]
            };
    return validWindows

def windowEnumerationHandler(windowId, validWindows):
    rect = list(win32gui.GetWindowRect(windowId))
    rect[2] = rect[2] - rect[0]
    rect[3] = rect[3] - rect[1]
    if win32gui.IsWindowVisible(windowId):
        validWindows[win32gui.GetWindowText(windowId)] = {"id": windowId, "width": rect[2], "height": rect[3]}
    
def findWindowById(windowId):
    if operatingSystem == "Windows":
        return findWindowByIdWindows(windowId)
    elif operatingSystem == "Darwin":
        return findWindowByIdMacOSX(windowId)
    else:
        return findWindowByIdLinux(windowId)

def findWindowByIdWindows(windowId):
    if win32gui.IsWindow(windowId):
        rect = list(win32gui.GetWindowRect(windowId))
        rect[2] = rect[2] - rect[0]
        rect[3] = rect[3] - rect[1]
        return {win32gui.GetWindowText(windowId): {
            "id": windowId,
            "width": rect[2],
            "height": rect[3]
        }}
    return {}

def findWindowByIdMacOSX(windowId):
    windowInfo = CG.CGWindowListCopyWindowInfo(CG.kCGWindowListOptionIncludingWindow, windowId)
    if len(windowInfo) == 1:
        return {windowInfo[0]["kCGWindowOwnerName"] + " - " + windowInfo[0]["kCGWindowName"]: {
            "id":     windowInfo[0]["kCGWindowNumber"],
            "width":  windowInfo[0]["kCGWindowBounds"]["Width"],
            "height": windowInfo[0]["kCGWindowBounds"]["Height"]
        }}
    return {}

def findDesktop():
    if operatingSystem == "Windows":
        return findDesktopWindows()
    elif operatingSystem == "Darwin":
        return findDesktopMacOSX()
    else:
        return findDesktopLinux()

def findDesktopWindows():
    desktopId = win32gui.GetDesktopWindow()
    rect = list(win32gui.GetWindowRect(desktopId))
    rect[2] = rect[2] - rect[0]
    rect[3] = rect[3] - rect[1]
    return {win32gui.GetWindowText(desktopId): {
        "id": desktopId,
        "width": rect[2],
        "height": rect[3]
    }}
        
def findDesktopMacOSX():
    windowInfo = CG.CGWindowListCopyWindowInfo(CG.kCGWindowListOptionOnScreenOnly, CG.kCGNullWindowID)

    desktop = None
    for i in xrange(0, len(windowInfo)):
        if windowInfo[i]["kCGWindowName"] == "Desktop":
            desktop = {"id": windowInfo[i]["kCGWindowNumber"], "width":  windowInfo[i]["kCGWindowBounds"]["Width"], "height": windowInfo[i]["kCGWindowBounds"]["Height"]}
            break

    return desktop
