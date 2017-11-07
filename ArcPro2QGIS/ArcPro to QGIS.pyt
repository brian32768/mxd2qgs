from xml.dom.minidom import Document
from datetime import datetime
import arcpy

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [ArcProToQGIS]

class mxd2qgs(object):
    
    """Conversion wrapper.
    
    Class variables:
    proj -- The ArcPro Project
    doc -- The resultant document
    maps -- List of project Maps
    layouts -- List of project layouts (if any)"""

    def __init__(self):
        # Assign the input file
        try:
            self.proj = arcpy.mp.ArcGISProject("CURRENT")
        except (AssertionError, e):
            raise AssertionError('error importing' + "CURRENT" + ': ' + e.message)

        # Create the minidom
        self.doc = Document()

        # List of "Map" objects in the project
        self.maps = self.proj.listMaps()[0]
        self.layouts = self.proj.listLayouts()

    def convert(self):
        '''Run conversion and write to a file'''
        # Create the <qgis> base element
        qgis = self.doc.createElement("qgis")
        qgis.setAttribute("projectname", " ")
        qgis.setAttribute("version", "2.4.0-Chugiak")
        self.doc.appendChild(qgis)

        # Create the <title> element
        title = self.doc.createElement("title")
        qgis.appendChild(title)

        canvas = self.canvas()
        qgis.appendChild(canvas)

        legend = self.legend()
        qgis.appendChild(legend)

        layers = self.layers()
        qgis.appendChild(layers)
        # ArcPy documentation is quite insistent about deleting file references
        # Maybe something is wrong with their garbage collection?
        del(self.proj)

        # xml.dom.minidom.Document can't handle the !doctype
        return "<!DOCTYPE qgis PUBLIC 'https://svn.osgeo.org/qgis/trunk/qgis/qgis.dtd' 'SYSTEM'>" + linesep + self.doc.toxml()

    def createMapCanvas(self):
        '''Create the <mapcanvas> element'''

    def createProjectLayers(self):
        '''Create the <projectlayers> element'''
        layerlist = self.maps.ListLayers()
        layers = self.doc.createElement("projectlayers")
        layers.setAttribute("layercount", str(len(layerlist)))

        layertree = self.doc.createElement('layer-tree-group')
        treeDict = {'': layertree}

        for lyr in layerlist:
            name = str(lyr.name)
            parent_name = path.basename(path.dirname(lyr.longName))

            if lyr.isGroupLayer:
                treeLayer = self.setlayerprop(lyr, 'layer-tree-group')
                treeDict[name] = treeLayer

            else:
                ds = self.doc.createTextNode(str(lyr.dataSource))

                # Create the <maplayer> element
                maplayer = self.doc.createElement("maplayer")
                maplayer.setAttribute("minimumScale", "0")
                maplayer.setAttribute("maximumScale", "1e+08")
                maplayer.setAttribute("minLabelScale", "0")
                maplayer.setAttribute("maxLabelScale", "1e+08")

                # Create the <id> element
                # Use date to microsecond to produce unique id, as in QGIS
                _id = self.doc.createElement("id")
                _id.appendChild(self.doc.createTextNode(name + str(datetime.now().strftime('%Y%m%d%H%M%S%f'))))
                maplayer.appendChild(_id)

                treeLayer = self.setlayerprop(lyr, 'layer-tree-layer')
                treeLayer.setAttribute('id', _id)

                if(lyr.isRasterLayer == True):
                    maplayer.setAttribute("type", "raster")
                    pipe = self.doc.createElement('pipe')
                    rr = self.doc.createElement('rasterrenderer')
                    rr.setAttribute('opacity', lyr.transparency / 100.0)
                    pipe.appendChild(rr)
                    maplayer.appendChild(pipe)

                else:  # Is Vector
                    geotype = str(arcpy.Describe(lyr).shapeType)
                    maplayer.setAttribute("geometry", geotype)
                    maplayer.setAttribute("type", "vector")

                maplayer.setAttribute("hasScaleBasedVisibilityFlag", "0")
                maplayer.setAttribute("scaleBasedLabelVisibilityFlag", "0")

                # Create the <datasource> element
                datasource = self.doc.createElement("datasource")
                datasource.appendChild(ds)
                maplayer.appendChild(datasource)

                # Create the <layername> element
                layername = self.doc.createElement("layername")
                layername.appendChild(self.doc.createTextNode(name))
                maplayer.appendChild(layername)

                # Create the <srs> element
                srs = self.doc.createElement("srs")
                maplayer.appendChild(srs)

                spatialrefsys = self.generate_spatial(lyr)
                srs.appendChild(spatialrefsys)

                # Create the <transparencyLevelInt> element
                transparencyLevelInt = self.doc.createElement("transparencyLevelInt")
                transparencyLevelInt.appendChild(self.doc.createTextNode("255"))
                maplayer.appendChild(transparencyLevelInt)

                # Create the <customproperties> element
                customproperties = self.doc.createElement("customproperties")
                maplayer.appendChild(customproperties)

                # Create the <provider> element
                provider = self.doc.createElement("provider")
                provider.setAttribute("encoding", "System")
                ogr = self.doc.createTextNode("ogr")
                provider.appendChild(ogr)
                maplayer.appendChild(provider)

                # Create the <singlesymbol> element
                singlesymbol = self.doc.createElement("singlesymbol")
                maplayer.appendChild(singlesymbol)

                # Create the <symbol> element
                symbol = self.symbol()
                singlesymbol.appendChild(symbol)

                # Append to parent
                layers.appendChild(maplayer)

            layertree[parent_name].appendChild(treeLayer)

        return layers

    def canvas(self):
        '''Create the <mapcanvas> element'''
        mapcanvas = self.doc.createElement("mapcanvas")
        mapframe = self.layouts[0].listElements('MAPFRAME_ELEMENT'))
        cam = mapframe.camera

        # Create the <units> element
        unit = self.doc.createTextNode(self.df.mapUnits)

        units = self.doc.createElement("units")
        units.appendChild(unit)
        mapcanvas.appendChild(units)

        # Create the <extent> element
        extent = self.doc.createElement("extent")
        mapcanvas.appendChild(extent)

        # Create the <xmin> element
        xmin = self.doc.createElement("xmin")
        xmin.appendChild(self.doc.createTextNode(str(cam.getExtent().XMin)))
        extent.appendChild(xmin)

        # Create the <ymin> element
        ymin = self.doc.createElement("ymin")
        ymin.appendChild(self.doc.createTextNode(str(cam.getExtent().YMin)))
        extent.appendChild(ymin)

        # Create the <xmax> element
        xmax = self.doc.createElement("xmax")
        xmax.appendChild(self.doc.createTextNode(str(cam.getExtent().XMax)))
        extent.appendChild(xmax)

        # Create the <ymax> element
        ymax = self.doc.createElement("ymax")
        ymax.appendChild(self.doc.createTextNode(str(cam.getExtent().YMax)))
        extent.appendChild(ymax)

        # Create the <projections> element
        projections = self.doc.createElement("projections")
        mapcanvas.appendChild(projections)

        # Create the <destinationsrs> element
        destinationsrs = self.doc.createElement("destinationsrs")
        mapcanvas.appendChild(destinationsrs)

        # Create the <spatialrefsys> element
        spatialrefsys = self.generate_spatial(mapframe)
        destinationsrs.appendChild(spatialrefsys)

        return mapcanvas

    def generate_spatial(self, lyr):
        '''Generate spatial references for the document or a layer'''
        spatialrefsys = self.doc.createElement("spatialrefsys")
        sr = arcpy.Describe(lyr).spatialReference

        # Create the <proj4> element
        proj4 = self.doc.createElement("proj4")
        spatialrefsys.appendChild(proj4)

        # Create the <srsid> element
        srsid = self.doc.createElement("srsid")
        spatialrefsys.appendChild(srsid)

        # Create the <srid> element
        mxd_srid = self.doc.createTextNode(str(sr.factoryCode))
        srid = self.doc.createElement("srid")
        srid.appendChild(mxd_srid)
        spatialrefsys.appendChild(srid)

        # Create the <authid> element
        mxd_authid = self.doc.createTextNode("EPSG:" + str(sr.factoryCode))
        authid = self.doc.createElement("authid")
        authid.appendChild(mxd_authid)
        spatialrefsys.appendChild(authid)

        # Create the <description> element
        max_d = self.doc.createTextNode(str(sr.name))
        description = self.doc.createElement("description")
        description.appendChild(max_d)
        spatialrefsys.appendChild(description)

        # Create the <projectionacronym> element
        projectionacronym = self.doc.createElement("projectionacronym")
        spatialrefsys.appendChild(projectionacronym)

        # Create the <ellipsoidacronym element
        ea = self.doc.createTextNode(str(sr.name))
        ellipsoidacronym = self.doc.createElement("ellipsoidacronym")
        ellipsoidacronym.appendChild(ea)
        spatialrefsys.appendChild(ellipsoidacronym)

        # Create the <geographicflag> element
        geographicflag = self.doc.createElement("geographicflag")
        geographicflag.appendChild(self.doc.createTextNode("true"))
        spatialrefsys.appendChild(geographicflag)

        return spatialrefsys

    def legend(self):
        '''Create the <legend> element'''
        legend = self.doc.createElement("legend")
        mapLayers = self.maps.ListLayers()

        for lyr in mapLayers:
            if (lyr.isGroupLayer == False):

                # Create the <legendlayer> element
                legendlayer = self.doc.createElement("legendlayer")
                legendlayer.setAttribute("open", "true")
                legendlayer.setAttribute("checked", "Qt::Checked")
                legendlayer.setAttribute("name", str(lyr.name))

                legend.appendChild(legendlayer)

                # Create the <filegroup> element
                filegroup = self.doc.createElement("filegroup")
                filegroup.setAttribute("open", "true")
                filegroup.setAttribute("hidden", "false")
                legendlayer.appendChild(filegroup)

                # Create the <legendlayerfile> element
                legendlayerfile = self.doc.createElement("legendlayerfile")
                legendlayerfile.setAttribute("isInOverview", "0")
                legendlayerfile.setAttribute("layerid", str(lyr.name) + str(20110427170816078))
                legendlayerfile.setAttribute("visible", "1")
                filegroup.appendChild(legendlayerfile)

        return legend

    def setlayerprop(self, layer, treeElemName):
        tree = self.doc.createElement(treeElemName)

        if layer.supports('visible'):
            if layer.visible:
                checked = 'Qt::Checked'
            else:
                checked = 'Qt::Unchecked'

            tree.setAttribute('checked', checked)
            tree.setAttribute('name', str(layer.name))

        return tree

    def symbol(self):
        '''Create and populate a dummy symbol element'''
        symbol = self.doc.createElement("symbol")
        # Create the <lowervalue> element
        symbol.appendChild(self.doc.createElement("lowervalue"))

        # Create the <uppervalue> element
        symbol.appendChild(self.doc.createElement("uppervalue"))

        # Create the <label> element
        symbol.appendChild(self.doc.createElement("label"))

        # Create the <rotationclassificationfieldname> element
        rotationclassificationfieldname = self.doc.createElement("rotationclassificationfieldname")
        symbol.appendChild(rotationclassificationfieldname)

        # Create the <scaleclassificationfieldname> element
        scaleclassificationfieldname = self.doc.createElement("scaleclassificationfieldname")
        symbol.appendChild(scaleclassificationfieldname)

        # Create the <symbolfieldname> element
        symbol.appendChild(self.doc.createElement("symbolfieldname"))

        # Create the <outlinecolor> element
        outlinecolor = self.doc.createElement("outlinecolor")
        outlinecolor.setAttribute("red", "88")
        outlinecolor.setAttribute("blue", "99")
        outlinecolor.setAttribute("green", "37")
        symbol.appendChild(outlinecolor)

        # Create the <outlinestyle> element
        outlinestyle = self.doc.createElement("outlinestyle")
        outline = self.doc.createTextNode("SolidLine")
        outlinestyle.appendChild(outline)
        symbol.appendChild(outlinestyle)

        # Create the <outlinewidth> element
        outlinewidth = self.doc.createElement("outlinewidth")
        width = self.doc.createTextNode("0.26")
        outlinewidth.appendChild(width)
        symbol.appendChild(outlinewidth)

        # Create the <fillcolor> element
        # Todo: correct colors"
        fillcolor = self.doc.createElement("fillcolor")
        fillcolor.setAttribute("red", "90")
        fillcolor.setAttribute("blue", "210")
        fillcolor.setAttribute("green", "229")
        symbol.appendChild(fillcolor)

        # Create the <fillpattern> element
        fillpattern = self.doc.createElement("fillpattern")
        fill = self.doc.createTextNode("SolidPattern")
        fillpattern.appendChild(fill)
        symbol.appendChild(fillpattern)

        # Create the <texturepath> element
        texturepath = self.doc.createElement("texturepath")
        texturepath.setAttribute("null", "1")
        symbol.appendChild(texturepath)


class ArcProToQGIS(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Save to .gis file format"
        self.description = "Tool to use for saving an ArcPro Project to a Quantum GIS File"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        outputFile = arcpy.Parameter (
            displayName="GIS Output File",
            name="GIS_Output_File",
            datatype="File",
            parameterType="Required",
            direction="Output"
        )
        params = [outputFile]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        converter = mxd2qgs()
        outfile = parameters[0].valueAsText
        converter.convert()
        return
