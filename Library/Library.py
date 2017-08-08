# Simple
# Easy to use
# Little to no setup
# Customizable

# SUPPORTED STRUCTURE
# Library
# -- Type
# ---- Object


# SETTINGS
# File Type
# Import location
# Project Path

# TODO: Right click to update screenshot
# TOOD: Hide not selection



try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
    from flowLayout2 import *
except ImportError:
    from PySide.QtCore import *
    from PySide.QtGui import *
    from shiboken import wrapInstance
    from flowLayout import *

from maya import OpenMayaUI as omui
import pymel.core as pm
import shutil
import os
import sys
import subprocess
import ConfigParser
import re
import unicodedata


class Ui_Settings(QWidget):
    def __init__(self, parent=None):
        super(Ui_Settings, self).__init__()
        self.verticalLayout = QVBoxLayout(self)
        self.horizontalLayout = QHBoxLayout()
        self.label = QLabel(self)
        self.horizontalLayout.addWidget(self.label)
        self.lineEdit = QLineEdit(self)
        self.horizontalLayout.addWidget(self.lineEdit)
        self.pushButton = QPushButton(self)
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacer_item = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacer_item)

        self.setWindowTitle("Settings")
        self.label.setText("Library Location:")
        self.pushButton.setText("...")


class Ui_Library(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(Ui_Library, self).__init__(*args, **kwargs)
        self.resize(800, 600)
        self.main_layout = QWidget(self)
        self.vertical_layout = QVBoxLayout(self.main_layout)
        self.tabWidget = QTabWidget(self.main_layout)
        self.export_layout = QHBoxLayout()
        spacer_item = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.export_label = QLabel()
        self.export_label.setText("Category")

        self.export_combo_box = QComboBox(self.main_layout)
        self.export_combo_box.setInsertPolicy(QComboBox.InsertAlphabetically)
        self.export_combo_box.setEditable(True)

        self.export_button = QPushButton(self.main_layout)
        self.export_button.clicked.connect(self.export)

        self.menu_bar = QMenuBar()
        self.menu_bar.setGeometry(QRect(0, 0, 800, 22))
        self.menu_file = QMenu(self.menu_bar)
        self.setMenuBar(self.menu_bar)
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.action_settings = QAction(self)
        self.action_exit = QAction(self)

        self.setCentralWidget(self.main_layout)
        self.vertical_layout.addWidget(self.tabWidget)
        self.export_layout.addItem(spacer_item)
        self.export_layout.addWidget(self.export_label)
        self.export_layout.addWidget(self.export_combo_box)
        self.export_layout.addWidget(self.export_button)
        self.vertical_layout.addLayout(self.export_layout)
        self.menu_file.addAction(self.action_settings)
        self.menu_file.addAction(self.action_exit)
        self.menu_bar.addAction(self.menu_file.menuAction())

        self.setWindowTitle("Library")
        self.menu_file.setTitle("File")
        self.action_settings.setText("Settings")
        self.action_exit.setText("Exit")
        self.export_button.setText("Export Selected")

        self.tabWidget.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(self)


class Settings(Ui_Settings):
    def __init__(self, parent=None):
        self.parent = parent
        self.config_path = self.get_save_location()
        super(Settings, self).__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.lineEdit.setText(str(self.library_path))
        self.pushButton.clicked.connect(self.browse)
        self.lineEdit.returnPressed.connect(self.location_updated)

    @staticmethod
    def get_save_location(name="MayaLibrary"):
        if sys.platform.startswith("win"):
            path = os.getenv('LOCALAPPDATA')
            path = os.path.join(path, name)
        elif sys.platform.startswith("darwin"):
            path = os.path.expanduser('~/Library/Application Support/')
            path = os.path.join(path, name)
        else:
            path = os.getenv('XDG_DATA_HOME', os.path.expanduser("~/.local/share"))
            path = os.path.join(path, name)
        return path

    def read_config(self):
        try:
            conf = ConfigParser.RawConfigParser()
            conf.read(self.config_path)
            save_file = conf.get("settings", "library")
            return save_file
        except ConfigParser.NoSectionError:
            self.create_config()
            return False
        except ConfigParser.MissingSectionHeaderError:
            self.create_config()
            return False
        except ConfigParser.NoOptionError:
            self.create_config()
            return False

    def get_library_path(self):
        path = self.lineEdit.text()
        if os.path.exists(path):
            return path

    def create_config(self):
        lib_path = self.get_library_path()
        config = ConfigParser.RawConfigParser()
        config.add_section('settings')
        config.set('settings', 'library', lib_path)
        self.parent.library_path = lib_path
        with open(self.config_path, 'wb') as configfile:
            config.write(configfile)

    def location_updated(self):
        self.create_config()
        self.parent.reset_ui()

    def browse(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec_():
            file_name = next(iter(dialog.selectedFiles()))
            self.lineEdit.setText(file_name)
            self.create_config()
            self.parent.reset_ui()

    @property
    def library_path(self):
        return self.read_config()


class Library(Ui_Library):
    def __init__(self, *args, **kwargs):
        super(Library, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.button_data = []
        self.library_path = ""
        self.__location = ""
        self.__object = None
        self.export_combo_box.currentIndexChanged.connect(self.add_category)
        self.tabWidget.currentChanged.connect(self.tab_change)
        self.action_settings.triggered.connect(self.show_settings_dialog)

        self.browse_action = QAction("Browse", self, triggered=self.browse)
        self.delete_tab_action = QAction("Delete", self, triggered=self.delete_tab)
        self.delete_button_action = QAction("Delete", self, triggered=self.delete_button)

        self.settings = Settings(self)
        self.settings.closeEvent = self.reset_ui
        self.library_path = self.settings.library_path

        self.reset_ui()

    def invalid_lib_path_error(self):
        self.status_bar.showMessage("Invalid Library path", 5000)

    def reset_ui(self, *args, **kwargs):
        self.button_data = []
        for i in xrange(self.tabWidget.count()):
            layout = self.tabWidget.widget(i).findChild(FlowLayout)
            layout.removeWidget(self.tabWidget.widget(i))
            self.tabWidget.widget(i).deleteLater()
        for i in xrange(self.export_combo_box.count()):
            self.export_combo_box.removeItem(i)

        if not os.path.exists(str(self.library_path)):
            return self.invalid_lib_path_error()

        self.setup_tabs()
        self.setup_category()

    def tab_change(self):
        category = self.tabWidget.tabText(self.tabWidget.currentIndex())
        self.export_combo_box.blockSignals(True)
        self.export_combo_box.setCurrentIndex(self.export_combo_box.findText(category))
        self.export_combo_box.blockSignals(False)

    def show_settings_dialog(self):
        self.error_shown = False
        self.settings.show()

    def contextMenuEvent(self, event):
        child = self.childAt(event.pos())
        if isinstance(child, QToolButton):
            self.button_menu(event)
        elif isinstance(child, QTabBar):
            self.tab_menu(event)

    def button_menu(self, event):
        c = self.tabWidget.currentWidget()
        b = c.childAt(c.mapFromGlobal(event.globalPos()))
        for x in self.button_data:
            if x["object"] == b:
                self.__location = x["folder"]
                self.__object = [b.parentWidget().layout(), b]

        menu = QMenu(self)
        menu.addAction(self.browse_action)
        menu.addAction(self.delete_button_action)
        menu.exec_(event.globalPos())

    def browse(self):
        if sys.platform.startswith("darwin"):
            subprocess.call(["open", "-R", self.__location])
        elif sys.platform.startswith("win"):
            subprocess.Popen('explorer "{0}"'.format(self.__location))

    def delete(self):
        i = len([_ for root, folder, files in os.walk(self.__location) for _ in files])

        if self.message_box("Delete Files",
                            "Are you sure you want to delete {} files?".format(i)) == QMessageBox.Ok:
            shutil.rmtree(self.__location)
            return True

    def delete_tab(self):
        if self.delete():
            self.export_combo_box.blockSignals(True)
            self.tabWidget.widget(self.__object).deleteLater()
            category = self.tabWidget.tabText(self.__object)
            self.export_combo_box.removeItem(self.export_combo_box.findText(category))
            self.export_combo_box.blockSignals(False)
            c = 0
            for b in self.button_data:
                if category in b["category"]:
                    self.button_data.remove(b)
                    c += 1
            self.status_bar.showMessage("Removed: {} objects".format(c), 5000)

    def delete_button(self):
        if self.delete():
            deleted = ""
            for b in self.button_data:
                if self.__location in b["path"]:
                    deleted = b["path"]
                    self.button_data.remove(b)
                    break
            self.__object[0].removeWidget(self.__object[1])
            self.__object[1].deleteLater()
            self.status_bar.showMessage("Removed: {}".format(deleted), 5000)

    def _get_clicked_tab_text(self, pos):
        bar = self.tabWidget.tabBar()
        for i in xrange(bar.count()):
            if bar.tabRect(i).contains(pos - QPoint(12, 33)):
                return self.tabWidget.tabText(i), i

    def tab_menu(self, event):
        category, tab = self._get_clicked_tab_text(event.pos())
        location = os.path.join(self.library_path, category)
        self.__location = location
        self.__object = tab

        menu = QMenu(self)
        menu.addAction(self.browse_action)
        menu.addAction(self.delete_tab_action)
        menu.exec_(event.globalPos())

    def setup_category(self):
        self.export_combo_box.blockSignals(True)
        for category in os.listdir(self.library_path):
            if os.path.isdir(os.path.join(self.library_path, category)):
                self.export_combo_box.addItem(category)
        self.export_combo_box.blockSignals(False)

    def add_category(self):
        if not os.path.exists(self.library_path):
            return self.invalid_lib_path_error()

        category = self.get_category_name()

        if not category and not self._get_tab_by_text(category):
            return        

        print(category, type(category))
        location = os.path.join(self.library_path, category)
        if not os.path.exists(location):
            os.makedirs(location)
        self.create_tab(category)

    @staticmethod
    def take_thumbnail(path):
        pm.playblast(percent=60, completeFilename="{}.jpg".format(path), viewer=False, forceOverwrite=True, frame=[1],
                     offScreen=True, compression="jpg", showOrnaments=False, format="image")

    def import_object(self):
        for x in self.button_data:
            if x["object"] == self.sender():
                pm.importFile(x["path"], type="mayaAscii", ignoreVersion=True, mergeNamespacesOnClash=False,
                              renamingPrefix="pCube1", options="v=0;", preserveReferences=True)
                break

    def export_object(self, category):
        selection = next(iter(pm.selected()), None)

        if not selection:
            return
        name = slugify(selection.name())
        location = os.path.join(os.path.join(self.library_path, category), name)
        if not os.path.exists(location):
            os.makedirs(location)
        pm.exportSelected("{}.ma".format(os.path.join(location, name)), type='mayaAscii', options="v=0;",
                          force=True)

        return os.path.join(location, name)

    def export(self):
        if not os.path.exists(str(self.library_path)):
            return self.invalid_lib_path_error()

        category = self.get_category_name()
        if not category:
            return

        export_path = self.export_object(category)
        if export_path:
            self.take_thumbnail(export_path)
            self.refresh_category(category)
            self.status_bar.showMessage(export_path, 5000)
        else:
            self.status_bar.showMessage("Nothing selected", 5000)

    @staticmethod
    def button_meta_data(object_location):
        data_img = ""
        data_file = ""
        for file_name in os.listdir(object_location):
            object_path = os.path.join(object_location, file_name)
            if os.path.isfile(object_path):
                if object_path.endswith(".jpg") or object_path.endswith(".png"):
                    data_img = object_path
                elif object_path.endswith(".ma"):
                    data_file = object_path
        return data_img, data_file

    def import_button(self, parent, object_location):
        img, path = self.button_meta_data(object_location)

        font = QFont()
        font.setPointSize(18)
        btn = QToolButton()
        btn.setFont(font)
        btn.setAutoRaise(True)
        btn.setText(os.path.basename(path).split(".")[0])
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.clicked.connect(self.import_object)
        btn.setIcon(QIcon(img))
        btn.setMaximumSize(120, 120)
        btn.setIconSize(QSize(120, 120))

        parent.addWidget(btn)

        self.button_data.append({"object": btn, "icon": img, "path": path,
                                 "folder": object_location, "parent": parent,
                                 "category": os.path.basename(os.path.dirname(object_location))})

    def create_buttons(self, widget, type_location):
        for dir_name in os.listdir(type_location):
            object_path = os.path.join(type_location, dir_name)
            if os.path.isdir(object_path):
                self.import_button(widget, object_path)

    def _iterate_button(self, attr):
        for btn in self.button_data:
            yield btn[attr]

    def _get_tab_by_text(self, category):
        for i in xrange(self.tabWidget.count()):
            if self.tabWidget.tabText(i) == category:
                return self.tabWidget.widget(i).findChild(FlowLayout)

    def refresh_category(self, category):
        tab = self._get_tab_by_text(category)
        if not tab:
            tab = self.create_tab(category)

        category_folder = os.path.join(self.library_path, category)
        for folder in os.listdir(category_folder):
            object_folder = os.path.join(category_folder, folder)
            if os.path.isdir(object_folder) and object_folder not in self._iterate_button("folder"):
                self.import_button(tab, object_folder)

    def create_tab(self, name):
        tab = QWidget()

        layout = QHBoxLayout(tab)
        scroll_area = QScrollArea(tab)
        scroll_area.setWidgetResizable(True)
        scroll_area_widget_contents = QWidget()
        scroll_area_widget_contents.setGeometry(QRect(0, 0, 728, 476))
        scroll_area.setWidget(scroll_area_widget_contents)
        layout.addWidget(scroll_area)

        grid_layout = FlowLayout(scroll_area_widget_contents)
        self.tabWidget.addTab(tab, "")
        self.tabWidget.setTabText(self.tabWidget.count() - 1, name)

        return grid_layout

    def setup_tabs(self):
        if not os.path.exists(str(self.library_path)):
            return self.invalid_lib_path_error()

        for dir_name in os.listdir(self.library_path):
            type_path = os.path.join(self.library_path, dir_name)
            if os.path.isdir(type_path):
                tab = self.create_tab(dir_name)
                self.create_buttons(tab, type_path)

    def message_box(self, text, informative_text):
        msg_box = QMessageBox(self)
        msg_box.setText(text)
        msg_box.setInformativeText(informative_text)
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Ok)
        return msg_box.exec_()

    def get_category_name(self):
        category = self.export_combo_box.currentText()

        if not category and slugify(category) == category.lower():
            self.status_bar.showMessage("Invalid category name", 5000)
            return None

        self.export_combo_box.blockSignals(True)
        if self.export_combo_box.findText(category, Qt.MatchFlag.MatchFixedString) == -1:
            self.export_combo_box.addItem(category.lower())
        self.export_combo_box.setCurrentIndex(self.export_combo_box.findText(category, Qt.MatchFlag.MatchFixedString))
        self.export_combo_box.setItemText(self.export_combo_box.findText(category), category.lower())
        self.export_combo_box.blockSignals(False)

        return category.lower()


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    value = unicode(re.sub('[-\s]+', '-', value))
    return value


def convert_ui():
    from pysideuic import compileUi
    pyfile = open("/Users/mattias.hedberg/Documents/repo/presto_util/production/library/window.py", 'w')
    compileUi("/Users/mattias.hedberg/Documents/repo/presto_util/production/library/main.ui", pyfile, False, 4,
              False)
    pyfile.close()

    
def main():
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)
    ui = Library()
    ui.show()
    
    
if __name__ == '__main__':
    main()


