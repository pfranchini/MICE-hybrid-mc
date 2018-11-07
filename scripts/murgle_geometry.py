import xml.etree.ElementTree
import glob
import os

class GeometryMurgler(object):
    def __init__(self, tracker_geometry):
        self.geometry = tracker_geometry
        self.tracker = None

    def murgle(self):
        self.target_dir = self.geometry["target_dir"]
        self.src_dir = self.geometry["source_dir"]
        self.ref_dir = self.geometry["reference_dir"]
        self.tracker = 0
        if self.geometry["tracker"] == "tkd":
            self.tracker = 1
        self.move_tracker(self.geometry["position"], self.geometry["rotation"])
        self.tracker_material_density(self.geometry["density"], self.geometry["silicon_fraction"])
        self.scale_field(self.geometry["scale"])
       
    def rescale(self, line, new_scale):
        words = line.split(" ")
        value = float(words[-1])*new_scale
        words[-1] = str(value)
        line = " ".join(words)
        return line

    def scale_field(self, scale):
        solenoid = ["SSU", "SSD"][self.tracker]
        fin = open(self.src_dir+"/ParentGeometryFile.dat")
        lines = [line.rstrip() for line in fin.readlines()]
        fin.close()
        for coil, new_scale in scale.iteritems():
            subname = solenoid+coil+"Current"
            for i, line in enumerate(lines):
                if line.find(subname) > 0 and line.find("Substitution") > 0:
                    lines[i] = self.rescale(line, new_scale)

        fout = open(self.target_dir+"/ParentGeometryFile.dat.tmp", "w")
        for line in lines:
            fout.write(line+'\n')
        fout.close()
        os.rename(self.target_dir+"/ParentGeometryFile.dat.tmp", self.target_dir+"/ParentGeometryFile.dat")


    def get_element_recursive_child(self, element_src, tag, required_attributes):
        """
        Get element which has a child with given tag and attributes
        - element_src: check recursively for children in this elements
        - tag: string tag. Returns element_src if one of its children has tag
        - required_attributes: dictionary. Returns element_src if one of its 
          children has all attributes in required_attributes with matching value
          If you don't want to check value, set to None.
        """
        for child in element_src:
            if child.tag == tag:
                for key in required_attributes:
                    if key not in child.attrib:
                        continue
                    if required_attributes[key] == None or \
                       required_attributes[key] == child.attrib[key]:
                        return element_src
            else:
                volume = self.get_element_recursive_child(child, tag, required_attributes)
                if volume != None:
                    return volume

    def get_element_recursive(self, element_src, tag, required_attributes):
        """
        Get element which has given tag and attributes
        - element_src: check recursively for children in this elements
        - tag: string tag. Returns element_src with this tag
        - required_attributes: dictionary. Returns element_src if it has all 
          attributes in required_attributes with matching value
          If you don't want to check value, set to None.
        """
        if element_src.tag == tag:
            for key in required_attributes:
                if key not in element_src.attrib:
                    continue
                if required_attributes[key] == None or \
                    required_attributes[key] == element_src.attrib[key]:
                    return element_src
        else:
            for child in element_src:
                element = self.get_element_recursive(child, tag, required_attributes)
                if element != None:
                    return element
      

    def move_tracker(self, position, rotation):
        """
        Apply a translation and rotation to the tracker
        - position: translate the tracker by the given distance, in addition to
          any default translation
        - rotation: rotate the tracker by the given angle, in addition to any
          default rotation
        """
        if self.tracker == 0:
            src_filename = self.src_dir+"/SolenoidUS.gdml"
            target_filename = self.target_dir+"/SolenoidUS.gdml"
            tracker_filename = self.ref_dir+"/Tracker0.gdml"
        else:
            src_filename = self.src_dir+"/SolenoidDS.gdml"
            target_filename = self.target_dir+"/SolenoidDS.gdml"
            tracker_filename = self.ref_dir+"/Tracker1.gdml"
        tree = xml.etree.ElementTree.parse(src_filename)
        volume = self.get_element_recursive_child(tree.getroot(), "file", {"name":tracker_filename})
        if volume == None:
            raise RuntimeError("Failed to find tag "+tracker_filename+" in "+src_filename)
        for child in volume:
            delta = {}
            if child.tag == "position":
                delta = position
            elif child.tag == "rotation":
                delta = rotation
            else:
                continue
            attrib = child.attrib
            for axis in delta:
                new_value = float(attrib[axis])+delta[axis]
                attrib[axis] = repr(new_value)
            child.attrib = attrib
        tree.write(target_filename+".tmp")
        os.rename(target_filename+".tmp", target_filename)

    def add_silicon(self, tree):
        """
        Add silicon to the tracker <materials> tag
        """
        material = self.get_element_recursive_child(tree.getroot(),
                                                    "material",
                                                    {"name":"TrackerGlue"})
        if material == None:
            raise RuntimeError("Failed to find materials element")
        # source: wikipedia
        silicon = xml.etree.ElementTree.Element("element", attrib={"name":"RogersSi"})
        index = -1
        for item in material:
            if material.get("name") == "TrackerGlue":
                break
            index += 1
        for n, mass, fraction in [("28", "28.085", "0.922"),
                                  ("29", "28.085", "0.047"),
                                  ("30", "28.085", "0.031")]:
            name = "RogersSi"+n
            z = "14"
            silicon_at = xml.etree.ElementTree.Element("atom", attrib={"unit":"g/mole", "value":mass})
            silicon_is = xml.etree.ElementTree.Element("isotope", attrib={"N":n, "Z":z, "name":name})
            silicon_is.append(silicon_at)
            material.insert(index, silicon_is)
            index += 1
            silicon_fr = xml.etree.ElementTree.Element("fraction", attrib={"n":fraction, "ref":name})
            silicon.append(silicon_fr)
        material.insert(index, silicon)

    def modify_glue(self, tree, density, si_content):
        """
        Modify the glue to contain appropriate density and silicon fraction
        """
        material = self.get_element_recursive_child(tree.getroot(),
                                                    "material",
                                                    {"name":"TrackerGlue"})
        if material == None:
            raise RuntimeError("Failed to find materials element")
        # move the old glue out of the way
        default_glue = self.get_element_recursive(material,
                                                  "material",
                                                  {"name":"TrackerGlue"})
        default_glue.set("name", "TrackerGlueBase")
        # add in glue that is a mixture of base and silicon
        glue = xml.etree.ElementTree.Element("material",
                                attrib={"name":"TrackerGlue", "formula":"glue"})
        # density element
        density = str(density)
        density_element = xml.etree.ElementTree.Element("D",
                                attrib={"value":str(density), "unit":"g/cm3"})
        # glue_base_fraction
        glue_content = str(1-si_content)
        glue_base_fraction = xml.etree.ElementTree.Element("fraction",
                                    {"n":glue_content, "ref":"TrackerGlueBase"})
        glue.append(density_element)
        glue.append(glue_base_fraction)
        if si_content > 0.:
            si_content = str(si_content)
            silicon_fraction = xml.etree.ElementTree.Element("fraction",
                                        {"n":si_content, "ref":"RogersSi"})
            glue.append(silicon_fraction)
        material.append(glue)

    def tracker_material_density(self, density, si_content):
        src_filename_glob = self.src_dir+"/Tracker"+str(self.tracker)+"View?Station?_Doublet.gdml"
        for src_filename in glob.glob(src_filename_glob):
            tree = xml.etree.ElementTree.parse(src_filename)
            self.add_silicon(tree)
            self.modify_glue(tree, density, si_content)
            target_filename = os.path.join(self.target_dir, os.path.split(src_filename)[1])
            for element in tree.getroot():
                self.indent(element)
            tree.write(target_filename+".tmp")
            os.rename(target_filename+".tmp", target_filename)

    def indent(self, elem, level=0):
        """
        Add indentation to elementtree (found on stacktrace)
        """
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
