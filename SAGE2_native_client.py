import sys
import argparse
import time
import numpy as np
from Tkinter import *
from PIL import Image, ImageTk
from threading import Timer

sys.path.append("./src")

from windowfinder import *
from screencapture import *
from websocketio import *


wsio = None
captureData = None
appId = None

def main():
    global captureData

    parser = argparse.ArgumentParser(description="SAGE2 Native Application Streaming Client")
    parser.add_argument("-w", "--window",     type=str, nargs='?', default=None, help="id of window to capture")
    parser.add_argument("-r", "--region",     type=str, nargs='?', default=None, help="x,y,w,h - region of screen to capture")
    parser.add_argument("-f", "--fullscreen", action='store_true',               help="x,y,w,h - region of screen to capture")
    parser.add_argument("-d", "--hidpi",      action='store_true',               help="enable HiDPI mode on compatible devices")
    parser.add_argument("-a", "--address",    type=str, nargs='?', default=None, help="ip address / hostname to connect with")
    parser.add_argument("-s", "--secure",     action='store_true',               help="whether of not to create secure connection")
    args = parser.parse_args()
    

    # all info entered at command line
    if (args.fullscreen or args.region != None or args.window != None) and args.address != None:
        captureType = None
        region = None
        windowId = None
        if args.fullscreen:
            desktop = findDesktop()
            windowTitle = "SAGE2 Stream - Full Screen"
            captureData = {"type": "fullscreen", "width": int(desktop["width"]), "height": int(desktop["height"]), "title": windowTitle, "enableHiDPI": args.hidpi};
            startSAGE2Streaming(args.address)
        elif args.region != None:
            rect = [ int(x) for x in args.region.split(",") ]
            windowTitle = "SAGE2 Stream - Region: " + str(rect[0]) + "," + str(rect[1]) + " " + str(rect[2]) + "," + str(rect[3])
            captureData = {"type": "region", "rect": rect, "width": rect[2], "height": rect[3], "title": windowTitle, "enableHiDPI": args.hidpi}
            startSAGE2Streaming(args.address)
        else:
            windows = findWindowById(int(args.window))
            if bool(windows):
                windowTitle = list(windows.keys())[0]
                captureData = {"type": "window", "id": windows[windowTitle]["id"], "width": int(windows[windowTitle]["width"]), "height": int(windows[windowTitle]["height"]), "title": windowTitle, "enableHiDPI": args.hidpi}
                startSAGE2Streaming(args.address)
            else:
                print "Error: could not find window with id " + args.window

    # otherwise open dialog box to prompt user
    else:
        windows = findAllWindows()

        root = Tk()
        app = SAGE2NativeAppStreamerGUI(root, windows)
        if args.region != None:
            app.updateRegionEntries([ int(x) for x in args.region.split(",") ], True)
        elif args.window != None:
            selected = findWindowById(int(args.window))
            if bool(selected):
                app.updateWindowOption(list(selected.keys())[0])
        if args.address != None:
            app.updateAddress(args.address)
        if args.hidpi != False:
            app.enableHiDPI.set(1)
        app.updateCapturePreview()
        root.mainloop()
        root.destroy()

        if app.launch:
            if app.captureOption.get() == "*Full Screen":
                desktop = findDesktop()
                windowTitle = "SAGE2 Stream - Full Screen"
                captureData = {"type": "fullscreen", "width": int(desktop["width"]), "height": int(desktop["height"]), "title": windowTitle, "enableHiDPI": app.enableHiDPI.get() == 1}
            elif app.captureOption.get() == "*Region":
                windowTitle = "SAGE2 Stream - Region: " + app.regionX["var"].get() + "," + app.regionY["var"].get() + " " + app.regionW["var"].get() + "," + app.regionH["var"].get()
                captureData = {"type": "region", "rect": [ int(app.regionX["var"].get()), int(app.regionY["var"].get()), int(app.regionW["var"].get()), int(app.regionH["var"].get()) ], "width": int(app.regionW["var"].get()), "height": int(app.regionH["var"].get()), "title": windowTitle, "enableHiDPI": app.enableHiDPI.get() == 1}
            else:
                captureData = {"type": "window", "id": windows[app.captureOption.get()]["id"], "width": int(windows[app.captureOption.get()]["width"]), "height": int(windows[app.captureOption.get()]["height"]), "title": app.captureOption.get(), "enableHiDPI": app.enableHiDPI.get() == 1}
            startSAGE2Streaming(app.address["var"].get())

def startSAGE2Streaming(address):
    global wsio
    global captureData

    img = captureImage()
    w,h = img.size
    captureData["native_width"] = w
    captureData["native_height"] = h

    wsio = WebSocketIO("ws://" + address)
    wsio.open(on_open) # starts in new thread, and waits indefinitely to listen

def on_open():
    global wsio

    wsio.on("initialize", wsInitialize)
    wsio.on("requestNextFrame", wsRequestNextFrame)
    wsio.on("stopMediaCapture", wsStopMediaCapture)

    wsio.emit("addClient", {"clientType": "NativeAppStreamer", "requests": {"config": False, "version": False, "time": False, "console": False}})

def wsInitialize(data):
    global wsio
    global captureData
    global appId

    appId = data["UID"]
    if captureData["enableHiDPI"]:
        wsio.emit("startNewMediaBlockStream", {"id": appId + "|0", "width": captureData["native_width"], "height": captureData["native_height"], "title": captureData["title"], "color": "#FFFFFF", "colorspace": "RGBA"})
    else:
        wsio.emit("startNewMediaBlockStream", {"id": appId + "|0", "width": captureData["width"], "height": captureData["height"], "title": captureData["title"], "color": "#FFFFFF", "colorspace": "RGBA"})

def wsRequestNextFrame(data):
    global captureData

    img = captureImage()
    iw = captureData["native_width"]
    ih = captureData["native_height"]

    if captureData["enableHiDPI"] == False and (captureData["width"] != captureData["native_width"] or captureData["height"] != captureData["native_height"]):
        img = img.resize((captureData["width"], captureData["height"]), Image.ANTIALIAS)
        iw = captureData["width"]
        ih = captureData["height"]

    pix = np.ravel(np.asarray(img)) # RGBA array [R G B A R G B A ... R G B A]
    if pix.size != (4*iw*ih):
        wsRequestNextFrame(data)
        return;

    idBuf = np.fromstring(appId + "|0\x00", dtype=np.uint8)
    finalBuf = np.concatenate((idBuf, pix))
    wsio.emit("updateMediaBlockStreamFrame", finalBuf)

def wsStopMediaCapture(data):
    global wsio

    print "stopping media capture"
    wsio.close()

def captureImage():
    global captureData

    img = None
    if captureData["type"] == "fullscreen":
        img = screenshot()
    elif captureData["type"] == "region":
        img = screenshot(region=captureData["rect"])
    elif captureData["type"] == "window":
        img = screenshot(window=captureData["id"])
    else:
        print "Error: capture type \"" + captureData["type"] + "\" not recognized"

    return img


class SAGE2NativeAppStreamerGUI(Frame):
    def __init__(self, parent, options):
        Frame.__init__(self, parent, background="#FFFFFF")
        self.parent = parent
        self.launch = False
        self.initUI(options)
    
    def initUI(self, windows):
        self.parent.title("SAGE2 Native App Streamer")
        self.parent.resizable(0,0)
        self.pack(fill=BOTH, expand=1)
        self.centerWindow()

        self.windows = windows
        self.validateInteger = (self.parent.register(self.isNonNegativeInteger), "%d", "%i", "%P", "%s", "%S", "%v", "%V", "%W")

        self.setupWindowOptions()
        self.setupRegionEntry()
        self.setupAddressEntry()

        self.enableHiDPI = IntVar(self)
        hidpiCheckbox = Checkbutton(self, text="Enable HiDPI Mode", variable=self.enableHiDPI)
        hidpiCheckbox.pack()
        hidpiCheckbox.place(x=440, y=300)

        startButton = Button(self, text="Start", command=self.start, font="Arial 14", width=6, height=1)
        startButton.place(x=440, y=370)
        quitButton = Button(self, text="Quit", command=self.quit, font="Arial 14", width=6, height=1)
        quitButton.place(x=520, y=370)

        default = ImageTk.PhotoImage(Image.open("data/images/default.jpg").resize((336, 189), Image.ANTIALIAS))
        self.previewImage = Label(self, image=default, highlightbackground="#000000", highlightthickness=1)
        self.previewImage.image = default
        self.previewImage.place(x=12, y=196)

    def centerWindow(self):
        w = 600
        h = 400

        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()
        
        x = (sw - w)/2
        y = (sh - h)/2

        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def setupWindowOptions(self):
        options = list(self.windows.keys())
        options.insert(0, "*Region")
        options.insert(0, "*Full Screen")

        windowLabel = Label(self, text="Capture:", font="Arial 14 bold")
        windowLabel.pack()
        windowLabel.place(x=10, y=12)
        self.captureOption = StringVar(self)
        self.captureOption.set(options[0])
        self.captureOption.trace("w", self.windowOptionChanged)
        windowOption = OptionMenu(self, self.captureOption, *options)
        windowOption.pack()
        windowOption.config(width=40, font="Arial 14")
        windowOption.place(x=82, y=32)

    def setupRegionEntry(self):
        self.regionLabel = Label(self, text="Region:", font="Arial 14 bold")
        self.regionLabel.pack()
        self.regionLabel.place(x=10, y=70)
        self.regionLabel.config(state="disabled")
        self.regionX = self.addTextEntry("x:", "0",  86, 90, 6, self.validateInteger)
        self.regionX["label"].config(state="disabled")
        self.regionX["entry"].config(state="disabled")
        self.regionY = self.addTextEntry("y:", "0", 166, 90, 6, self.validateInteger)
        self.regionY["label"].config(state="disabled")
        self.regionY["entry"].config(state="disabled")
        self.regionW = self.addTextEntry("width:", "1280", 266, 90, 6, self.validateInteger)
        self.regionW["label"].config(state="disabled")
        self.regionW["entry"].config(state="disabled")
        self.regionH = self.addTextEntry("height:", "720", 376, 90, 6, self.validateInteger)
        self.regionH["label"].config(state="disabled")
        self.regionH["entry"].config(state="disabled")

    def setupAddressEntry(self):
        addressLabel = Label(self, text="Address:", font="Arial 14 bold")
        addressLabel.pack()
        addressLabel.place(x=10, y=128)
        self.address = self.addTextEntry("hostname / ip:", "127.0.0.1",  86, 148, 24)

    def addTextEntry(self, labelText, entryText, x, y, width, validate=None):
        aLabel = Label(self, text=labelText, font="Arial 14")
        aLabel.pack()
        aLabel.place(x=x, y=y+2)
        variable = StringVar(self)
        aEntry = None
        if validate == None:
            aEntry = Entry(self, textvariable=variable)
        else:
            aEntry = Entry(self, textvariable=variable, validate="key", validatecommand=validate)
        aEntry.config(width=width)
        aEntry.pack()
        aEntry.place(x=x+7*len(labelText), y=y)
        aEntry.insert(0, entryText)
        return {"var": variable, "entry": aEntry, "label": aLabel}

    def start(self):
        self.launch = True
        self.quit()

    def windowOptionChanged(self, *args):
        if self.captureOption.get() == "*Region":
            self.regionLabel.config(state="normal")
            self.regionX["label"].config(state="normal")
            self.regionX["entry"].config(state="normal")
            self.regionY["label"].config(state="normal")
            self.regionY["entry"].config(state="normal")
            self.regionW["label"].config(state="normal")
            self.regionW["entry"].config(state="normal")
            self.regionH["label"].config(state="normal")
            self.regionH["entry"].config(state="normal")
        else:
            self.regionLabel.config(state="disabled")
            self.regionX["label"].config(state="disabled")
            self.regionX["entry"].config(state="disabled")
            self.regionY["label"].config(state="disabled")
            self.regionY["entry"].config(state="disabled")
            self.regionW["label"].config(state="disabled")
            self.regionW["entry"].config(state="disabled")
            self.regionH["label"].config(state="disabled")
            self.regionH["entry"].config(state="disabled")

        self.updateCapturePreview()

    def updateCapturePreview(self):
        self.capturePreview().save("data/images/preview.jpg", quality=90, format="JPEG")
        pImg = Image.open("data/images/preview.jpg")
        pW,pH = pImg.size
        pAspect = float(pW) / float(pH)
        fW = int(189.0 * pAspect)
        fH = 189
        if fW >= 400:
            fW = 400
            fH = int(400.0 / pAspect)
        preview = ImageTk.PhotoImage(pImg.resize((fW, fH), Image.ANTIALIAS))
        self.previewImage.config(image=preview)
        self.previewImage.image = preview

    def capturePreview(self):
        preview = None
        if self.captureOption.get() == "*Full Screen":
            preview = screenshot()
        elif self.captureOption.get() == "*Region":
            rect = [ int(self.regionX["var"].get()), int(self.regionY["var"].get()), int(self.regionW["var"].get()), int(self.regionH["var"].get()) ]
            preview = screenshot(region=rect)
        else:
            preview = screenshot(window=self.windows[self.captureOption.get()]["id"])
        return preview

    def updateRegionEntries(self, region, enabled):
        self.regionX["var"].set(str(region[0]))
        self.regionY["var"].set(str(region[1]))
        self.regionW["var"].set(str(region[2]))
        self.regionH["var"].set(str(region[3]))

        if enabled:
            self.captureOption.set("*Region")
            self.regionLabel.config(state="normal")
            self.regionX["label"].config(state="normal")
            self.regionX["entry"].config(state="normal")
            self.regionY["label"].config(state="normal")
            self.regionY["entry"].config(state="normal")
            self.regionW["label"].config(state="normal")
            self.regionW["entry"].config(state="normal")
            self.regionH["label"].config(state="normal")
            self.regionH["entry"].config(state="normal")

    def updateWindowOption(self, window):
        self.captureOption.set(window)

    def updateAddress(self, address):
        self.address["var"].set(address)

    def isNonNegativeInteger(self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
        if value_if_allowed == "":
            return True
        try:
            val = int(value_if_allowed)
            if val >= 0:
                return True
            else:
                return False
        except ValueError:
            return False

    """
    # Capture full screen
    fullscreen = screenshot()
    fullscreen.save("fullscreen.jpg", quality=90, format="JPEG")
    #fpix = np.ravel(np.asarray(fullscreen.convert("RGB"))) # RGB array [R G B R G B ... R G B]


    # Capture region (200x200 box, 50 from top and 50 from left)
    region = screenshot(region=CG.CGRectMake(50, 50, 200, 200))
    region.save("region.jpg", quality=90, format="JPEG")
    #rpix = np.ravel(np.asarray(region.convert("RGB"))) # RGB array [R G B R G B ... R G B]
    """
"""
captureImages = []

def main():
    captureScreen(0)

def captureScreen(frame): 
    global captureImages


    start = time.time()

    ci = screenshot()
    captureImages.append(ci)

    end = time.time()

    print "frame " + str(frame) + ": " + str(end-start)

    if frame < 50:
        t = Timer(0.040, captureScreen, [frame+1])
        t.start()
    else:
        saveCapturedImages()

def saveCapturedImages():
    global captureImages

    for i in xrange(0, len(captureImages)):
        captureImages[i].save("capture%02d.jpg" % i, quality=90, format="JPEG")
"""

main()
