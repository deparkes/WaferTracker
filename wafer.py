#!/usr/bin/python

from gi.repository import Gtk, Gdk, cairo, Pango, PangoCairo
import math
import sys, os
import numpy as np
import cPickle as pickle
import xml.etree.cElementTree as et

def autoconvert(s):
    for fn in (int, float):
        try:
            return fn(s)
        except ValueError:
            pass
    return s

class Sample():
    def __init__(self, sampleName):
        self.name = sampleName
        self.sizeX = 0.0
        self.sizeY = 0.0
        self.thick = 0.0
        self.notes = ""
        self.status = 3 # 3 Unmeasured, 2 Dead, 1 Alive
    def __str__(self):
        return self.name
    def setStatus(self, status):
        if self.status == status and self.status != 3:
            self.status = 3
        else:
            self.status = status

class Die():
    def __init__(self, dieName, rows, cols,
                 startingRowLetter='1', startingColLetter="A"):
        self.name = dieName
        self.notes = ""
        self.status = -1
        self.rows = rows
        self.cols = cols

        self.thickTopLeft  = 0.0
        self.thickTopRight = 0.0
        self.thickBotRight = 0.0
        self.thickBotLeft  = 0.0

        # Create the array of samples
        self.samples = [[Sample(chr(ord(startingColLetter)+i)+chr(ord(startingRowLetter)+j)) for j in range(self.rows)] for i in range(self.cols)]

    def __str__(self):
        return self.name

class Wafer():
    def __init__(self, waferName, waferRows, waferCols, dieRows, dieCols,
                 startingRowLetter='1', startingColLetter="Q"):
        self.name         = waferName
        self.notes        = ""
        self.status       = -1
        self.waferRows    = waferRows
        self.waferCols    = waferCols
        self.dieRows      = dieRows
        self.dieCols      = dieCols

        self.dieSpacingX  = 10.0 # distance between exposures in mm
        self.dieSpacingY  = 10.0
        self.sampleSpacingX = 0.75 # distance between samples in mm
        self.sampleSpacingY = 0.75

        self.SampleMargin = 2    # For display only
        self.DieMargin    = 15   # For display only
        self.wedge        = 0 # 0 None, 1 Left to Right, 2 Right to left, 3 Bottom to top, 4 top to bottom

        # Create the array of dies
        self.dies = [[Die(chr(ord(startingColLetter)+i)+chr(ord(startingRowLetter)+j), self.dieRows, self.dieCols) for j in range(self.waferRows)] for i in range(self.waferCols)]

class WaferDisplay(Gtk.DrawingArea):

    def __init__ (self, upper=9, text=''):
        Gtk.DrawingArea.__init__(self)
        self.set_size_request (800, 800)
        self.wafer = Wafer("Test", 5, 5, 5, 7)
        self.builder = Gtk.Builder()
        self.builder.add_from_file("interface.glade")
        self.filename = ""

    def loadWithArg(self, filename):
        self.filename = filename
        self.parseXML()

    def load(self, event):
        dialog = Gtk.FileChooserDialog("Please choose a file", self.get_toplevel(),
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.filename = dialog.get_filename()
            self.parseXML()
        dialog.destroy()
        
    def save(self, event):
        if self.filename == "":
            self.saveas(event)
        else:
            self.generateXML()

    def saveas(self, event):
        dialog = Gtk.FileChooserDialog("Please choose a file", self.get_toplevel(),
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.filename = dialog.get_filename()
            self.generateXML()
        dialog.destroy()

    def generateXML(self):
        root = et.Element("wafer")
        root.set("name"   , str(self.wafer.name))
        root.text = self.wafer.notes
        root.set("status"   ,str(self.wafer.status))
        root.set("waferRows",str(self.wafer.waferRows))
        root.set("waferCols",str(self.wafer.waferCols))
        root.set("dieRows"  ,str(self.wafer.dieRows))
        root.set("dieCols"  ,str(self.wafer.dieCols))
        root.set("wedge"    ,str(self.wafer.wedge))
        root.set("dieSpacingX",    str(self.wafer.dieSpacingX))
        root.set("dieSpacingY",    str(self.wafer.dieSpacingY))
        root.set("sampleSpacingX", str(self.wafer.sampleSpacingX))
        root.set("sampleSpacingY", str(self.wafer.sampleSpacingY))
        
        for i in range(self.wafer.waferCols):
            wafcol = et.SubElement(root, "wafcol")
            for j in range(self.wafer.waferRows):
                dieObj = self.wafer.dies[i][j]
                die = et.SubElement(wafcol, "die")
                die.text = dieObj.notes
                die.set("status",str(dieObj.status))
                die.set("name"  ,str(dieObj.name))
                die.set("rows"  ,str(dieObj.rows))
                die.set("cols"  ,str(dieObj.cols))
                die.set("thickTopLeft",  str(dieObj.thickTopLeft))
                die.set("thickTopRight", str(dieObj.thickTopRight))
                die.set("thickBotRight", str(dieObj.thickBotRight))
                die.set("thickBotLeft",  str(dieObj.thickBotLeft))
                
                for ii in range(self.wafer.dieCols):
                    diecol = et.SubElement(die, "diecol")
                    for jj in range(self.wafer.dieRows):
                        devObj = self.wafer.dies[i][j].samples[ii][jj]
                        device = et.SubElement(diecol, "device")
                        device.text = devObj.notes
                        device.set("status",str(devObj.status))
                        device.set("name"  ,str(devObj.name))
                        device.set("thick" ,str(devObj.thick))
                        device.set("sizeX" ,str(devObj.sizeX))
                        device.set("sizeY" ,str(devObj.sizeY))
                            
        tree = et.ElementTree(root)
        tree.write(self.filename, encoding="utf-8", xml_declaration=True)

    def parseXML(self):
        tree = et.parse(self.filename)
        root = tree.getroot()
        wrows = int(root.get("waferRows"))
        wcols = int(root.get("waferCols"))
        drows = int(root.get("dieRows"))
        dcols = int(root.get("dieCols"))
        self.wafer = Wafer(root.get("name"), wrows, wcols, drows, dcols)
        self.wafer.status = int(root.get("status"))
        self.wafer.wedge  = int(root.get("wedge"))
        if not root.get("dieSpacingX") is None:
            self.wafer.dieSpacingX    = float(root.get("dieSpacingX")   ) 
        if not root.get("dieSpacingY") is None:
            self.wafer.dieSpacingY    = float(root.get("dieSpacingY")   ) 
        if not root.get("sampleSpacingX") is None:
            self.wafer.sampleSpacingX = float(root.get("sampleSpacingX"))
        if not root.get("sampleSpacingY") is None:
            self.wafer.sampleSpacingY = float(root.get("sampleSpacingY"))

        notes = root.text
        if notes == None:
            notes = ""
        self.wafer.notes = notes

        for i, wafcol in enumerate(root.findall('wafcol')):
            for j, die in enumerate(wafcol.findall('die')):
                for item in die.items():
                    name, val = item
                    if val is not None:
                        setattr(self.wafer.dies[i][j], name, autoconvert(val))
                    notes = die.text
                    if notes == None:
                        notes = ""
                    self.wafer.dies[i][j].notes = notes
                    if not die.get("thickTopLeft") is None:
                        self.wafer.dies[i][j].thickTopLeft  = float(die.get("thickTopLeft")) 
                    if not die.get("thickTopRight") is None:
                        self.wafer.dies[i][j].thickTopRight = float(die.get("thickTopRight"))
                    if not die.get("thickBotRight") is None:
                        self.wafer.dies[i][j].thickBotRight = float(die.get("thickBotRight")) 
                    if not die.get("thickBotLeft") is None:
                        self.wafer.dies[i][j].thickBotLeft  = float(die.get("thickBotLeft"))
  
                for ii, diecol in enumerate(die.findall('diecol')):
                    for jj, device in enumerate(diecol.findall('device')):
                        for item in device.items():
                            name, val = item
                            if val is not None:
                                setattr(self.wafer.dies[i][j].samples[ii][jj], name, autoconvert(val))
                            notes = device.text
                            if notes == None:
                                notes = ""
                            self.wafer.dies[i][j].samples[ii][jj].notes = notes
                            if not device.get("thick") is None:
                                self.wafer.dies[i][j].samples[ii][jj].thick = float(device.get("thick") )
                            if not device.get("sizeX") is None:
                                self.wafer.dies[i][j].samples[ii][jj].sizeX = float(device.get("sizeX") )
                            if not device.get("sizeY") is None:
                                self.wafer.dies[i][j].samples[ii][jj].sizeY = float(device.get("sizeY") )

    def _(self, name):
        """Get the GTK object from the builder"""
        return self.builder.get_object(name)

    def do_draw_cb(self, widget, cr):
        self.get_toplevel().set_title("Wafer Tracker - "+self.wafer.name)

        rect = self.get_allocation()
        w = rect.width
        h = rect.height
        rad = 0.5*min(w,h)-10.0
        cr.translate ( 0.5*w, 0.5*h)
        usefulBoxSize = rad*1.3

        # Draw wafer with flat
        cr.move_to( rad*np.cos(250.0*np.pi/180.0),  rad*np.sin(250.0*np.pi/180.0))
        cr.line_to( rad*np.cos(290.0*np.pi/180.0),  rad*np.sin(290.0*np.pi/180.0))
        cr.arc(0.0, 0.0, rad, 290.0*np.pi/180.0, 250.0*np.pi/180.0)
        cr.set_line_width(3)
        cr.set_source_rgb(0., 6./16., 1.0)
        cr.stroke_preserve()
        cr.set_source_rgb(0.8, 0.8, 0.8)
        cr.fill()

        # Draw wedge
        ubs = usefulBoxSize
        if self.wafer.wedge == 1:
            cr.move_to(-0.5*ubs, 0.5*ubs + 10)
            cr.line_to( 0.5*ubs, 0.5*ubs + 10)
            cr.line_to( 0.5*ubs, 0.5*ubs + 25)
            cr.line_to(-0.5*ubs, 0.5*ubs + 10)
            cr.set_source_rgb(0., 6./16., 1.0)
            cr.stroke()
        elif self.wafer.wedge == 2:
            ubs = usefulBoxSize
            cr.move_to(-0.5*ubs, 0.5*ubs + 10)
            cr.line_to(-0.5*ubs, 0.5*ubs + 25)
            cr.line_to( 0.5*ubs, 0.5*ubs + 10)
            cr.line_to(-0.5*ubs, 0.5*ubs + 10)
            cr.set_source_rgb(0., 6./16., 1.0)
            cr.stroke()
        elif self.wafer.wedge == 4:
            ubs = usefulBoxSize
            cr.move_to(0.5*ubs + 10, -0.5*ubs )
            cr.line_to(0.5*ubs + 10,  0.5*ubs )
            cr.line_to(0.5*ubs + 25,  0.5*ubs )
            cr.line_to(0.5*ubs + 10, -0.5*ubs )
            cr.set_source_rgb(0., 6./16., 1.0)
            cr.stroke()
        elif self.wafer.wedge == 3:
            ubs = usefulBoxSize
            cr.move_to(0.5*ubs + 10, -0.5*ubs )
            cr.line_to(0.5*ubs + 25, -0.5*ubs )
            cr.line_to(0.5*ubs + 10,  0.5*ubs )
            cr.line_to(0.5*ubs + 10, -0.5*ubs )
            cr.set_source_rgb(0., 6./16., 1.0)
            cr.stroke()

        DieSizeX = (usefulBoxSize - (self.wafer.waferCols-1)*self.wafer.DieMargin)/self.wafer.waferCols
        DieSizeY = (usefulBoxSize - (self.wafer.waferRows-1)*self.wafer.DieMargin)/self.wafer.waferRows
        for i in range(self.wafer.waferCols):
            for j in range(self.wafer.waferRows):
               
                # Draw Dies
                transX = (i-0.5*(self.wafer.waferCols-1))*(DieSizeX+self.wafer.DieMargin)-0.5*DieSizeX
                transY = (j-0.5*(self.wafer.waferRows-1))*(DieSizeY+self.wafer.DieMargin)-0.5*DieSizeY
                cr.rectangle(transX-4, transY-4, DieSizeX+8, DieSizeY+8)
                cr.set_line_width(1.0)
                if self.wafer.dies[i][j].notes == "":
                    cr.set_source_rgb(0.1, 0.1, 0.1)
                else:
                    cr.set_source_rgb(0., 6./16., 1.0)
                cr.stroke()

                # Draw Label
                if j==0:
                    layout = PangoCairo.create_layout(cr)
                    layout.set_text(chr(ord("Q")+i), -1)
                    desc = Pango.font_description_from_string ( "Sans Bold 24" )
                    layout.set_font_description( desc)
                    cr.set_source_rgb(0.0, 0.0, 0.0)
                    cr.save()
                    cr.move_to( transX + DieSizeX*0.32, transY - 0.6*DieSizeY)
                    PangoCairo.show_layout (cr, layout)
                    cr.restore()
                if i==0:
                    layout = PangoCairo.create_layout(cr)
                    layout.set_text(chr(ord("1")+j), -1)
                    desc = Pango.font_description_from_string ( "Sans Bold 24" )
                    layout.set_font_description( desc)
                    cr.set_source_rgb(0.0, 0.0, 0.0)
                    cr.save()
                    cr.move_to( transX - 0.6*DieSizeX, transY + 0.35*DieSizeY)
                    PangoCairo.show_layout (cr, layout)
                    cr.restore()

                # Draw devices
                for ii in range(self.wafer.dieCols):
                    for jj in range(self.wafer.dieRows):
                        SampSizeX = (DieSizeX - 2*self.wafer.SampleMargin - (self.wafer.dieCols-1)*self.wafer.SampleMargin)/self.wafer.dieCols 
                        SampSizeY = (DieSizeY - 2*self.wafer.SampleMargin - (self.wafer.dieRows-1)*self.wafer.SampleMargin)/self.wafer.dieRows 
                        transXX = ii*(SampSizeX+self.wafer.SampleMargin)+ transX + self.wafer.SampleMargin
                        transYY = jj*(SampSizeY+self.wafer.SampleMargin)+ transY + self.wafer.SampleMargin
                        cr.rectangle(transXX, transYY, SampSizeX, SampSizeY)
                        cr.set_line_width(0.5)
                        if self.wafer.dies[i][j].samples[ii][jj].status == 1:
                            cr.set_source_rgb(0.0, 0.8, 0.0)
                            cr.fill()
                        elif self.wafer.dies[i][j].samples[ii][jj].status == 2:
                            cr.set_source_rgb(0.8, 0.0, 0.0)
                            cr.fill()
                        cr.set_source_rgb(0.2, 0.2, 0.2)
                        cr.stroke()
                        if self.wafer.dies[i][j].samples[ii][jj].notes != "":
                            cr.set_source_rgb(0.1, 0.1, 0.1)
                            cr.arc(transXX + 0.5*SampSizeX, transYY + 0.5*SampSizeY, 2, 0, 2.0*np.pi)
                            cr.fill()

                        # Labels
                        if i==0 and j==0:
                            if jj==0:
                                layout = PangoCairo.create_layout(cr)
                                layout.set_text(chr(ord("A")+ii), -1)
                                desc = Pango.font_description_from_string ( "Sans 10" )
                                layout.set_font_description(desc)
                                cr.save()
                                cr.move_to( transXX + SampSizeX*0.15, transYY - 1.1*SampSizeY - 6)
                                PangoCairo.show_layout (cr, layout)
                                cr.restore()
                            if ii==0:
                                layout = PangoCairo.create_layout(cr)
                                layout.set_text(chr(ord("1")+jj), -1)
                                desc = Pango.font_description_from_string ( "Sans 10" )
                                layout.set_font_description(desc)
                                cr.save()
                                cr.move_to( transXX - 1.1*SampSizeX - 6 , transYY + 0.15*SampSizeY)
                                PangoCairo.show_layout (cr, layout)
                                cr.restore()

    def openDeviceWindow(self, device):
        self._("sampleName").set_text(device.name)
        self._("sampleThick").set_value(device.thick)
        self._("sampleSizeX").set_value(device.sizeX)
        self._("sampleSizeY").set_value(device.sizeY)
        self._("sampleStatus").set_active(device.status-1)
        self._("sampleNotes").get_buffer().set_text(device.notes)
        dialogResponse = self._("deviceWindow").run()
        if dialogResponse == 0:
            device.thick  = self._("sampleThick").get_value()
            device.sizeX  = self._("sampleSizeX").get_value()
            device.sizeY  = self._("sampleSizeY").get_value()
            device.status = self._("sampleStatus").get_active()+1
            start         = self._("sampleNotes").get_buffer().get_start_iter()
            end           = self._("sampleNotes").get_buffer().get_end_iter()
            device.notes  = self._("sampleNotes").get_buffer().get_text(start, end, False)
        self._("deviceWindow").hide()

    def editDieWindow(self, die):
        self._("dieName1").set_text(die.name)
        self._("dieNotes").get_buffer().set_text(die.notes)
        self._("thickTopLeftAdj").set_value(die.thickTopLeft)
        self._("thickTopRightAdj").set_value(die.thickTopRight)
        self._("thickBotRightAdj").set_value(die.thickBotRight)
        self._("thickBotLeftAdj").set_value(die.thickBotLeft)
        dialogResponse = self._("dieWindow").run()
        if dialogResponse == 0:
            die.thickTopLeft  = self._("thickTopLeftAdj" ).get_value()
            die.thickTopRight = self._("thickTopRightAdj").get_value()
            die.thickBotRight = self._("thickBotRightAdj").get_value()
            die.thickBotLeft  = self._("thickBotLeftAdj" ).get_value()
            start         = self._("dieNotes").get_buffer().get_start_iter()
            end           = self._("dieNotes").get_buffer().get_end_iter()
            die.notes     = self._("dieNotes").get_buffer().get_text(start, end, False)
        self._("dieWindow").hide()

    def newWaferWindow(self, event):
        
        self._("wedgeType").set_active(0)
        dialogResponse = self._("newWindow").run()

        if dialogResponse == 0:
            name  = self._("waferNameEdit").get_text()
            dcols = int(self._("dieColsAdj").get_value())
            drows = int(self._("dieRowsAdj").get_value())
            scols = int(self._("sampColsAdj").get_value())
            srows = int(self._("sampRowsAdj").get_value())

            start = self._("waferNotes").get_buffer().get_start_iter()
            end   = self._("waferNotes").get_buffer().get_end_iter()

            self.wafer = Wafer(name, drows, dcols, srows, scols)
            self.wafer.wedge = int(self._("wedgeType").get_active())
            self.wafer.notes = self._("waferNotes").get_buffer().get_text(start, end, False)
            
            self.wafer.dieSpacingX    = self._("dieSpacingXAdj" ).get_value()
            self.wafer.dieSpacingY    = self._("dieSpacingYAdj").get_value()
            self.wafer.sampleSpacingX = self._("sampleSpacingXAdj").get_value()
            self.wafer.sampleSpacingY = self._("sampleSpacingAdjY" ).get_value()

            self.filename = ""

        self._("newWindow").hide()

    def editWaferWindow(self, event):

        self._("dieCols").set_sensitive(False)
        self._("dieRows").set_sensitive(False)
        self._("sampCols").set_sensitive(False)
        self._("sampRows").set_sensitive(False)
        self._("wedgeType").set_active(self.wafer.wedge)
        self._("waferNameEdit").set_text(self.wafer.name)
        self._("waferNotes").get_buffer().set_text(self.wafer.notes)

        self._("dieSpacingXAdj").set_value(    self.wafer.dieSpacingX    )
        self._("dieSpacingYAdj").set_value(    self.wafer.dieSpacingY    )
        self._("sampleSpacingXAdj").set_value( self.wafer.sampleSpacingX )
        self._("sampleSpacingYAdj" ).set_value(self.wafer.sampleSpacingY )

        dialogResponse = self._("newWindow").run()
        self._("dieCols").set_sensitive(True)
        self._("dieRows").set_sensitive(True)
        self._("sampCols").set_sensitive(True)
        self._("sampRows").set_sensitive(True)

        if dialogResponse == 0:
            dcols = int(self._("dieColsAdj").get_value())
            drows = int(self._("dieRowsAdj").get_value())
            scols = int(self._("sampColsAdj").get_value())
            srows = int(self._("sampRowsAdj").get_value())

            self.wafer.dieSpacingX    = self._("dieSpacingXAdj" ).get_value()
            self.wafer.dieSpacingY    = self._("dieSpacingYAdj").get_value()
            self.wafer.sampleSpacingX = self._("sampleSpacingXAdj").get_value()
            self.wafer.sampleSpacingY = self._("sampleSpacingYAdj" ).get_value()

            start = self._("waferNotes").get_buffer().get_start_iter()
            end   = self._("waferNotes").get_buffer().get_end_iter()

            #self.wafer = Wafer(name, drows, dcols, srows, scols)
            self.wafer.name  = self._("waferNameEdit").get_text()
            self.wafer.wedge = int(self._("wedgeType").get_active())
            self.wafer.notes = self._("waferNotes").get_buffer().get_text(start, end, False)
            
        self._("waferNotes").get_buffer().set_text("")
        self._("waferNameEdit").set_text("")
        self._("wedgeType").set_active(0)
        self._("newWindow").hide()

    def onclick (self, box, event):

        # Draw dies
        rect = self.get_allocation()
        w = rect.width
        h = rect.height
        rad = 0.5*min(w,h)-10.0
        usefulBoxSize = rad*1.3
        DieSizeX = (usefulBoxSize - (self.wafer.waferCols-1)*self.wafer.DieMargin)/self.wafer.waferCols
        DieSizeY = (usefulBoxSize - (self.wafer.waferRows-1)*self.wafer.DieMargin)/self.wafer.waferRows
        SampSizeX = (DieSizeX - 2*self.wafer.SampleMargin - (self.wafer.dieCols-1)*self.wafer.SampleMargin)/self.wafer.dieCols 
        SampSizeY = (DieSizeY - 2*self.wafer.SampleMargin - (self.wafer.dieRows-1)*self.wafer.SampleMargin)/self.wafer.dieRows 

        xclick, yclick = event.get_coords()
        xclick = xclick - 0.5*w 
        yclick = yclick - 0.5*h 

        hitSample = False
        for i in range(self.wafer.waferCols):
            transX = (i-0.5*(self.wafer.waferCols-1))*(DieSizeX+self.wafer.DieMargin)-0.5*DieSizeX
            if xclick > (transX-4) and xclick < (transX + DieSizeX+8):
                for j in range(self.wafer.waferRows):
                    transY = (j-0.5*(self.wafer.waferRows-1))*(DieSizeY+self.wafer.DieMargin)-0.5*DieSizeY
                    if yclick > (transY-4) and yclick < (transY + DieSizeY + 8):
                         # We've clicked on a die
                         for ii in range(self.wafer.dieCols):
                            transXX = ii*(SampSizeX+self.wafer.SampleMargin)+ transX + self.wafer.SampleMargin
                            if xclick > transXX and xclick < transXX + SampSizeX:
                                for jj in range(self.wafer.dieRows):
                                    transYY = jj*(SampSizeY+self.wafer.SampleMargin)+ transY + self.wafer.SampleMargin
                                    if yclick >= transYY and yclick <= transYY + SampSizeY:
                                        # We've clicked on a sample
                                        hitSample = True
                                        if event.button == 1:
                                            self.openDeviceWindow(self.wafer.dies[i][j].samples[ii][jj])
                                        if event.button > 1:
                                            self.wafer.dies[i][j].samples[ii][jj].setStatus(event.button-1)
                                        self.queue_draw()
                                        break
                         # But we didn't click on a sample
                         if hitSample == False:
                             self.editDieWindow(self.wafer.dies[i][j])

def destroy(window):
    Gtk.main_quit()
       
def main():
    
    builder = Gtk.Builder()
    builder.add_from_file("interface.glade")
    window = builder.get_object("mainWindow")
    box = builder.get_object("mainBox")

    app = WaferDisplay()

    if len(sys.argv) > 1:
        app.loadWithArg(sys.argv[1])
                      
    app.connect('draw', app.do_draw_cb)
    eventbox = Gtk.EventBox()
    eventbox.set_above_child(True)
    eventbox.connect("button-press-event", app.onclick)
    eventbox.add(app)
    box.pack_end(eventbox, True, True, 0)

    builder.get_object("newMenu").connect('activate', app.newWaferWindow)
    builder.get_object("saveMenu").connect('activate', app.save)
    builder.get_object("saveasMenu").connect('activate', app.saveas)
    builder.get_object("openMenu").connect('activate', app.load)
    builder.get_object("quitMenu").connect('activate', destroy)
    builder.get_object("menuWaferProps").connect('activate', app.editWaferWindow)
    window.connect_after('destroy', destroy)
    window.show_all()        
    Gtk.main()
       
if __name__ == "__main__":
    abspath = os.path.realpath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    sys.exit(main()) 
    