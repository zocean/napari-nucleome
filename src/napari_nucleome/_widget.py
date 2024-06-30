"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING, Union

from magicgui import magic_factory
from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSlider
from qtpy.QtWidgets import QGroupBox, QLabel, QLineEdit, QGridLayout
from qtpy.QtWidgets import QFileDialog
from qtpy.QtWidgets import QComboBox

from qtpy.QtCore import Signal, Qt

from pathlib import Path

import h5py

from napari._qt.widgets._slider_compat import QDoubleSlider

from napari_nucleome.utils import is_hdf5

if TYPE_CHECKING:
    import napari

import numpy as np
import pandas as pd

_logo_html = f"""
<h1>
<p>napari-nucleome</p>
<\h1>
"""

_docs_links_html = """
<h3>
<p>Atlas visualisation</p>
<p><a href="https://vis.nucleome.org" style="color:gray;">Website</a></p>
<p><a href="https://brainglobe.info/tutorials/visualise-atlas-napari.html" style="color:gray;">Tutorial</a></p>
<p><small>For help, hover the cursor over the atlases/regions.</small>
</h3>
""" 
# <p><a href="https://doi.org/10.7554/eLife.65751" style="color:gray;">Citation</a></p>
# <p><a href="https://github.com/brainglobe/brainrender-napari" style="color:gray;">Source</a></p>

def _logo_widget():
    return QLabel(_logo_html)


def _docs_links_widget():
    docs_links_widget = QLabel(_docs_links_html)
    docs_links_widget.setOpenExternalLinks(True)
    return docs_links_widget


def header_widget(parent: Union[QWidget, None]):
    box = QGroupBox(parent)
    box.setFlat(True)
    box.setLayout(QHBoxLayout())
    box.layout().addWidget(_logo_widget())
    box.layout().addWidget(_docs_links_widget())
    return box


class DataLoaderWidget(QWidget):
    add_data_request = Signal(str)
    def __init__(self, parent: Union[QWidget, None]):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        # define widgets
        file_browser_btn = QPushButton("Open data")
        file_browser_btn.clicked.connect(self.open_file_dialog)
        self.filename_edit = QLineEdit()
        # add widgets
        self.layout().addWidget(QLabel("File:"))
        self.layout().addWidget(self.filename_edit)
        self.layout().addWidget(file_browser_btn)
    def open_file_dialog(self):
        filename, ok = QFileDialog.getOpenFileName(
            self,
            caption='Open multiplexed FISH file',
            filter='HDF5 files (*.h5 *.hdf5 *.py)'
        )
        print(filename, ok)
        if filename:
            path = Path(filename)
            filename_base = path.stem
            self.filename_edit.setText(str(filename_base))
            self.add_data_request.emit(str(path))


class DataViewWidget(QWidget):
    add_probe_request = Signal(str)
    add_image_request = Signal(str)
    def __init__(self, parent: Union[QWidget, None]):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        ## define widgets
        # first row
        self.first_row = QGroupBox("", self) 
        self.first_row.setFlat(True)
        #self.first_row.setStyleSheet("QGroupBox { border: none; }")
        self.first_row.setLayout(QHBoxLayout())
        self.first_row.setContentsMargins(0, 0, 0, 0)
        self.first_row.layout().addWidget(QLabel("Status:"))
        self.status_bar_info = QLabel() # status bar
        self.first_row.layout().addWidget(self.status_bar_info)
        # second row
        self.second_row = QGroupBox("", self)
        self.second_row.setFlat(True)
        #self.second_row.setStyleSheet("QGroupBox { border: none; }")
        self.second_row.setLayout(QHBoxLayout())
        self.second_row.setContentsMargins(0, 0, 0, 0)
        self.second_row.layout().addWidget(QLabel("Probes:"))
        self.probe_dropdown = QComboBox() # probe set dropdown
        self.probe_dropdown.setToolTip("Select probe set")
        self.second_row.layout().addWidget(self.probe_dropdown)
        self.second_row.layout().addWidget(QLabel("Target:"))
        self.target_dropdown = QComboBox() # target dropdown
        self.target_dropdown.setToolTip("Select image or target")
        self.second_row.layout().addWidget(self.target_dropdown)
        # third row
        self.third_row = QGroupBox("", self)
        self.third_row.setFlat(True)
        #self.third_row.setStyleSheet("QGroupBox { border: none; }")
        self.third_row.setLayout(QHBoxLayout())
        self.third_row.setContentsMargins(0, 0, 0, 0)
        self.add_probe_btn = QPushButton("Add probes") # add probes button
        self.add_probe_btn.setToolTip("Add probes to the viewer")
        self.add_probe_btn.clicked.connect(self.handle_add_probe_request)
        self.add_target_image_btn = QPushButton("Add image") # add image button
        self.add_target_image_btn.setToolTip("Add target image to the viewer")
        self.add_target_image_btn.clicked.connect(self.handle_add_image_request)
        self.third_row.layout().addWidget(self.add_probe_btn)
        self.third_row.layout().addWidget(self.add_target_image_btn)
        # add widgets
        self.layout().addWidget(self.first_row)
        self.layout().addWidget(self.second_row)
        self.layout().addWidget(self.third_row)
    def handle_add_probe_request(self):
        probe_set = self.probe_dropdown.currentText()
        self.add_probe_request.emit(probe_set)
    def handle_add_image_request(self):
        target = self.target_dropdown.currentText()
        self.add_image_request.emit(target)


class ProbeNavWidget(QWidget):
    query_probe_request = Signal(str)
    reset_probe_request = Signal(str)
    set_probe_size_request = Signal(float)
    set_image_iso_request = Signal(float)
    def __init__(self, parent: Union[QWidget, None]):
        super().__init__(parent)
        self.setLayout(QGridLayout())
        # chrom
        self.layout().addWidget(QLabel('Chrom:'), 0, 0)
        self.chrom_dropdown = QComboBox() # probe chrom dropdown
        self.chrom_dropdown.setToolTip("Select chromosome")
        self.layout().addWidget(self.chrom_dropdown, 0, 1)
        # start
        self.layout().addWidget(QLabel('Start:'), 1, 0)
        self.start_edit = QLineEdit() 
        self.layout().addWidget(self.start_edit, 1, 1)
        # end
        self.layout().addWidget(QLabel('End:'), 2, 0)
        self.end_edit = QLineEdit()
        self.layout().addWidget(self.end_edit, 2, 1)
        # query button 
        self.query_probe_btn = QPushButton("Query Probe") # add probes button
        self.query_probe_btn.setToolTip("Filter probes to the viewer")
        self.query_probe_btn.clicked.connect(self.handle_query_probe_request) 
        self.layout().addWidget(self.query_probe_btn, 3, 0, 1, 2)
        self.reset_probe_btn = QPushButton("Reset probes") # add probes button
        self.reset_probe_btn.setToolTip("Reset probes to the viewer")
        self.reset_probe_btn.clicked.connect(self.handle_reset_probe_request)
        self.layout().addWidget(self.reset_probe_btn, 4, 0, 1, 2)
        # probe size
        self.layout().addWidget(QLabel('Probe size:'), 5, 0)
        self.probe_size_slider = QDoubleSlider(Qt.Orientation.Horizontal, parent=self)
        #self.probe_size_slider = QSlider(Qt.Horizontal)
        self.probe_size_slider.setMinimum(1)
        self.probe_size_slider.setMaximum(3)
        self.probe_size_slider.setToolTip("probe size")
        self.probe_size_slider.setSingleStep(0.1)
        self.probe_size_slider.valueChanged.connect(self.handle_probe_changeSize)
        self.layout().addWidget(self.probe_size_slider, 5, 1)
        # image iso
        self.layout().addWidget(QLabel('Z-score:'), 6, 0)
        self.image_iso_slider = QDoubleSlider(Qt.Orientation.Horizontal, parent=self)
        self.image_iso_slider.setToolTip("z-score cutoff")
        self.image_iso_slider.setMinimum(0)
        self.image_iso_slider.setMaximum(6)
        self.image_iso_slider.setSingleStep(0.01)
        self.image_iso_slider.valueChanged.connect(self.handle_image_changeIso)
        self.layout().addWidget(self.image_iso_slider, 6, 1)

    def handle_image_changeIso(self, value):
        self.set_image_iso_request.emit(value)

    def handle_probe_changeSize(self, value):
        self.set_probe_size_request.emit(value)
        
    def handle_reset_probe_request(self):
        self.reset_probe_request.emit('reset_all_probe')

    def handle_query_probe_request(self):
        probe_query_chrom = self.chrom_dropdown.currentText() 
        start_string = self.start_edit.text()
        end_string = self.end_edit.text()
        if start_string == '':
            start = 0
        else:
            try:
                start = int(start_string)
            except ValueError:
                print("Invalid start position: %s" % (start_string))
        if end_string == '':
            end = 1000000000 # 1 billion a large enough number
        else:
            try:
                end = int(end_string)
            except ValueError:
                print("Invalid end position: %s" % (end_string))
        probe_query_start = max(0, start)
        probe_query_end = max(0, end) 
        probe_coord = "%s:%d-%d" % (probe_query_chrom, probe_query_start, probe_query_end)
        self.query_probe_request.emit(probe_coord)


class NucleomeQWidget(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        ##############################
        # nucleome data
        ##############################
        self.data_probe_meta = {}
        self.probe_layer = None
        ##############################
        # create widgets 
        ##############################
        self.data_loader = DataLoaderWidget(self)
        self.data_view = DataViewWidget(self)
        self.probe_view = ProbeNavWidget(self)
        #self.probe_nav = Class of probes navigation
        # example button
        btn = QPushButton("Please, Click me!")
        btn.clicked.connect(self._on_click)
        # widget I: header
        self.setLayout(QVBoxLayout())
        #self.layout().addWidget(header_widget(self))
        # widget II: load data panel
        self.data_loader_group = QGroupBox("Load multiplexed FISH data", self)
        self.data_loader_group.setFlat(True)
        self.data_loader_group.setToolTip("Browser HDF5 file and load the data.")
        self.data_loader_group.setLayout(QVBoxLayout())
        self.data_loader_group.layout().addWidget(self.data_loader)
        self.layout().addWidget(self.data_loader_group)
        # widget III: data view panel
        self.data_view_group = QGroupBox("Add data to the viewer", self)
        self.data_view_group.setLayout(QVBoxLayout())
        self.data_view_group.layout().addWidget(self.data_view)
        self.layout().addWidget(self.data_view_group)
        # widget IV: probes navigation panel
        self.probe_nav_group = QGroupBox("Navigate probes", self)
        self.probe_nav_group.setLayout(QVBoxLayout())
        self.probe_nav_group.layout().addWidget(self.probe_view)
        self.layout().addWidget(self.probe_nav_group)
        ##############################
        # function to handle events
        ##############################
        self.data_loader.add_data_request.connect(self.add_data_meta_info)
        self.data_view.add_probe_request.connect(self.add_probe)
        self.data_view.add_image_request.connect(self.add_image)
        self.probe_view.query_probe_request.connect(self.query_probe)
        self.probe_view.reset_probe_request.connect(self.reset_probe)
        self.probe_view.set_probe_size_request.connect(self.set_probe_size)
        self.probe_view.set_image_iso_request.connect(self.set_image_iso)

    def set_probe_size(self, value):
        if self.probe_layer is not None:
            self.probe_layer.size = value

    def set_image_iso(self, value):
        if self.data_probe_meta.get("image_label", None) is not None:
            for image_label in self.data_probe_meta["image_label"]:
                if image_label in self.viewer.layers:
                    self.viewer.layers[image_label].iso_threshold = value

    def reset_probe(self, reset_type):
        if reset_type == 'reset_all_probe':
            if self.probe_layer is not None:
                self.probe_layer.shown = np.ones(len(self.probe_layer.data), dtype=bool)
                self.probe_layer.refresh()
    
    def add_data_meta_info(self, path):
        # update data view panel
        if path:
            # TODO use thread worder to deal with large dataset 
            self.data_view.status_bar_info.setText("Loading...")
            # check whether file is valid or not
            if is_hdf5(path):
                target_list = []
                probe_set_list = []
                with h5py.File(path, "r") as f:
                    # load probes
                    if "probes" in f.keys():
                        for probe_set in f["probes"].keys():
                            probe_set_list.append(probe_set)
                            # load meta
                            if "meta" in f["probes"][probe_set].keys():
                                self.data_view.status_bar_info.setText("Probe set %s loaded. Found %d probes." % (probe_set, np.array(f["probes/%s/meta/probe_count" %(probe_set)])))
                            else:
                                self.data_view.status_bar_info.setText("Invalid file: missing 'meta' group in %s" %(probe_set))
                    else:
                        self.data_view.status_bar_info.setText("Invalid file: missing 'probes' group in HDF5 file")
                    # load images/targets
                    if "targets" in f.keys():
                        if "data" in f["targets"].keys():
                            for key in f["targets"]["data"].keys():    
                                target_list.append(key)
                ## add probe set to probe-drop-down menu
                probe_dropdown = self.data_view.probe_dropdown
                # remove all items
                probe_dropdown.clear()
                # add probe set
                for probe_set in probe_set_list:
                    probe_dropdown.addItem(probe_set)
                ## add image set to image-drop-down menu
                target_dropdown = self.data_view.target_dropdown
                # remove all items
                target_dropdown.clear()
                # add new items
                for target in target_list:
                    target_dropdown.addItem(target)
                # 
                self.data_probe_meta["path"] = path
            else:
                self.data_view.status_bar_info.setText("Invalid file type: require valid HDF5 file")
        else:
            self.data_view.status_bar_info.setText("No data loaded")

    def query_probe(self, probe_coord):
        """
        probe_coord is a string, multiple position (chrom:start-end) are separated by comma
        """
        probe_list = [self.parse_probe_coord_string(coord) for coord in probe_coord.split(',')]
        if len(probe_list) > 0 and self.data_probe_meta.get("probe_properties", None) is not None:
            probe_properties = self.data_probe_meta["probe_properties"]
            # filter probe coordinates
            probe_list_final = None
            for probe in probe_list:
                probe_chrom = probe[0]
                probe_start = int(probe[1])
                probe_end = int(probe[2])
                probe_list = (probe_properties['chrom'] == probe_chrom) & (probe_properties['start'] >= probe_start) & (probe_properties['end'] < probe_end)
                if probe_list_final is None:
                    probe_list_final = probe_list
                else:
                    probe_list_final = probe_list_final | probe_list
            print("Found %d probes" % (sum(probe_list_final)))
            self.probe_layer.shown = probe_list_final
            if self.probe_view.probe_size_slider.value():
                self.probe_layer.size = self.probe_view.probe_size_slider.value()
            self.probe_layer.refresh()

    def parse_probe_coord_string(self, coord_string):
        chrom,start,end = coord_string.replace('-', ':').split(':')
        return (chrom, int(start), int(end))
    
    def add_probe(self, probe_set):
        chrom_list = ['chr1', 'chr2', 'chr3', 'chr4', 'chr5', 'chr6', 'chr7', 'chr8', 'chr9', 'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18', 'chr19', 'chr20', 'chr21', 'chr22', 'chrX', 'chrY']
        chrom2color = {'chr1': 'red',
                       'chr2': 'orangered', 
                       'chr3': 'peru',
                       'chr4': 'orange', 
                       'chr5': 'gold', 
                       'chr6': 'yellow', 
                       'chr7': 'olivedrab', 
                       'chr8': 'lawngreen', 
                       'chr9': 'lightgreen', 
                       'chr10': 'green', 
                       'chr11': 'lime', 
                       'chr12': 'turquoise', 
                       'chr13': 'teal', 
                       'chr14': 'cyan', 
                       'chr15': 'deepskyblue', 
                       'chr16': 'navy', 
                       'chr17': 'blue', 
                       'chr18': 'darkviolet', 
                       'chr19': 'purple', 
                       'chr20': 'deeppink',
                       'chr21': 'pink',
                       'chr22': 'brown',
                       'chrX': 'darkgrey',
                       'chrY': 'grey'
        }
        if probe_set and self.data_probe_meta.get("path", None) is not None:
            self.data_probe_meta["probe_set"] = probe_set
            with h5py.File(self.data_probe_meta["path"], "r") as f:
                # process probe location
                probe_zyx = np.array(f["probes"][probe_set]["zyx"]["data"])
                probe_properties = {'chrom':None, 'start':None, 'end':None, 'allele':None, 'probe_id':None}
                # process probe's properties
                probe_properties['chrom'] = [chrom.decode() for chrom in f["probes"][probe_set]['pos']['chrom']]
                probe_properties['start'] = np.array(f["probes"][probe_set]['pos']['start'])
                probe_properties['end'] = np.array(f["probes"][probe_set]['pos']['end'])
                probe_properties['probe_allele'] = [allele.decode() for allele in f["probes"][probe_set]['pos']['probe_allele']]
                probe_properties['probe_id'] = [probe_id.decode() for probe_id in f["probes"][probe_set]['pos']['probe_id']]
                probe_color = [chrom2color.get(chrom, 'grey') for chrom in probe_properties['chrom']]
                self.data_probe_meta["probe_properties"] = pd.DataFrame(probe_properties)
                self.probe_layer = self.viewer.add_points(probe_zyx, name = probe_set, properties = probe_properties, size = 1, edge_width = 0, face_color = probe_color)
            # get the chrom list and add them to the drop down menu in the probe navigation panel
            chrom_set = list(set(probe_properties['chrom'])) 
            self.data_probe_meta['chrom_list'] = [chrom for chrom in chrom_list if chrom in chrom_set]
            ## add probe set to probe-drop-down menu
            probe_chrom_dropdown = self.probe_view.chrom_dropdown
            # remove all items
            probe_chrom_dropdown.clear()
            # add probe set
            for chrom in self.data_probe_meta['chrom_list']:
                probe_chrom_dropdown.addItem(chrom)
            #probe_layer.mouse_move_callbacks.append(self._on_mouse_move)


    def add_image(self, image_label):
        if image_label and self.data_probe_meta.get("path", None) is not None:
            if self.data_probe_meta.get("image_label", None) is None:
                self.data_probe_meta["image_label"] = []
            self.data_probe_meta["image_label"].append(image_label)
            with h5py.File(self.data_probe_meta["path"], "r") as f:
                image_data = np.array(f["targets"]["data"][image_label])
                self.viewer.add_image(image_data, name=image_label, blending='translucent', rendering='iso')

    def _on_click(self):
        print("napari has", len(self.viewer.layers), "layers")


@magic_factory
def example_magic_widget(img_layer: "napari.layers.Image"):
    print(f"you have selected {img_layer}")


# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.
def example_function_widget(img_layer: "napari.layers.Image"):
    print(f"you have selected {img_layer}")
