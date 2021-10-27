import xml.etree.ElementTree as ET
import os, re


class Resource:
    def __init__(self, resource_tag):
        data = resource_tag.find("data")
        if data.attrib["encoding"] != "base64":
            raise NotImplementedError(
                self.__class__.__name__ + " not base64 encoded resource"
            )

        self.base64 = data.text.replace("\n", "").strip()


class Note:
    def __init__(self, note_tag):
        self.resource = None

        for property in note_tag:
            if property.tag in ("title", "created", "updated", "content"):
                setattr(self, property.tag, property.text)

            if property.tag == "resource":
                self.resource = Resource(property)

    def get_filename(self):
        return re.sub('[*"\/<>:|?]', "_", self.title) + ".html"

    def write_to_file(self, directory):
        target_path = os.path.join(directory, self.get_filename())

        with open(target_path, "w") as file:
            file.write(self.content)


class Notepad:
    def __init__(self, inputfile):
        self.root = ET.parse(inputfile).getroot()
        self.notes = []

        self.read_notes()
        print(str(self.notes))

    def read_notes(self):
        for note_tag in self.root.findall("note"):
            note = Note(note_tag)
            self.notes.append(note)
