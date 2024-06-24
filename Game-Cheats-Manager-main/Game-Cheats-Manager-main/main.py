import os
from queue import Queue
import shutil
import stat
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QFont, QFontDatabase, QIcon, QPixmap
from PyQt6.QtWidgets import QApplication, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QStatusBar, QVBoxLayout, QWidget
from tendo import singleton

from helper import *
from wemod import *
import style_sheet


class GameCheatsManager(QMainWindow):

    def __init__(self):
        super().__init__()

        # Single instance check and basic UI setup
        try:
            self.single_instance_checker = singleton.SingleInstance()
        except singleton.SingleInstanceException:
            sys.exit(1)
        except Exception as e:
            print(str(e))

        self.setWindowTitle("Game Cheats Manager")
        self.setWindowIcon(QIcon(resource_path("assets/logo.ico")))
        self.setMinimumSize(680, 520)

        # Version and links
        self.appVersion = "2.1.0"
        self.githubLink = "https://github.com/dyang886/Game-Cheats-Manager"
        self.updateLink = "https://api.github.com/repos/dyang886/Game-Cheats-Manager/releases/latest"
        self.bilibiliLink = "https://space.bilibili.com/256673766"

        # Paths and variable management
        self.trainerSearchEntryPrompt = tr("Search for installed")
        self.downloadSearchEntryPrompt = tr("Search to download")
        self.trainerDownloadPath = os.path.normpath(settings["downloadPath"])
        os.makedirs(self.trainerDownloadPath, exist_ok=True)
        
        if settings["theme"] == "black":
            self.dropDownArrow_path = resource_path("assets/dropdown-white.png").replace("\\", "/")
        elif settings["theme"] == "white":
            self.dropDownArrow_path = resource_path("assets/dropdown-black.png").replace("\\", "/")
        self.upArrow_path = resource_path("assets/up.png").replace("\\", "/")
        self.downArrow_path = resource_path("assets/down.png").replace("\\", "/")
        self.leftArrow_path = resource_path("assets/left.png").replace("\\", "/")
        self.rightArrow_path = resource_path("assets/right.png").replace("\\", "/")
        
        self.elevator_path = resource_path("dependency/elevator.exe")
        self.search_path = resource_path("assets/search.png")

        self.trainers = {}  # Store installed trainers: {trainer name: trainer path}
        self.searchable = True  # able to search online trainers or not
        self.downloadable = False  # able to double click on download list or not
        self.downloadQueue = Queue()
        self.currentlyDownloading = False
        self.currentlyUpdatingTrainers = False
        self.currentlyUpdatingFling = False
        self.currentlyUpdatingTrans = False

        # Window references
        self.settings_window = None
        self.about_window = None
        self.wemod_window = None

        # Main widget group
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        mainLayout = QGridLayout(centralWidget)
        mainLayout.setSpacing(15)
        mainLayout.setContentsMargins(30, 20, 30, 10)
        centralWidget.setLayout(mainLayout)
        self.init_settings()

        # Menu setup
        menu = self.menuBar()
        optionMenu = menu.addMenu(tr("Options"))

        settingsAction = QAction(tr("Settings"), self)
        settingsAction.triggered.connect(self.open_settings)
        optionMenu.addAction(settingsAction)

        importAction = QAction(tr("Import Trainers"), self)
        importAction.triggered.connect(self.import_files)
        optionMenu.addAction(importAction)

        openDirectoryAction = QAction(tr("Open Trainer Download Path"), self)
        openDirectoryAction.triggered.connect(self.open_trainer_directory)
        optionMenu.addAction(openDirectoryAction)

        whiteListAction = QAction(tr("Add Paths to Whitelist"), self)
        whiteListAction.triggered.connect(self.add_whitelist)
        optionMenu.addAction(whiteListAction)

        aboutAction = QAction(tr("About"), self)
        aboutAction.triggered.connect(self.open_about)
        optionMenu.addAction(aboutAction)

        # Below are standalone menu actions
        wemodAction = QAction(tr("WeMod Customization"), self)
        wemodAction.triggered.connect(self.wemod_pro)
        menu.addAction(wemodAction)

        updateDatabaseAction = QAction(tr("Update Trainer Database"), self)
        updateDatabaseAction.triggered.connect(self.fetch_database)
        menu.addAction(updateDatabaseAction)

        updateTrainersAction = QAction(tr("Update Trainers"), self)
        updateTrainersAction.triggered.connect(self.update_trainers)
        menu.addAction(updateTrainersAction)

        # Status bar setup
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # ===========================================================================
        # Column 1 - trainers
        # ===========================================================================
        trainersLayout = QVBoxLayout()
        trainersLayout.setSpacing(10)
        mainLayout.addLayout(trainersLayout, 0, 0)

        # Search installed trainers
        trainerSearchLayout = QHBoxLayout()
        trainerSearchLayout.setSpacing(10)
        trainerSearchLayout.setContentsMargins(20, 0, 20, 0)
        trainersLayout.addLayout(trainerSearchLayout)

        searchPixmap = QPixmap(self.search_path).scaled(25, 25, Qt.AspectRatioMode.KeepAspectRatio)
        searchLabel = QLabel()
        searchLabel.setPixmap(searchPixmap)
        trainerSearchLayout.addWidget(searchLabel)

        self.trainerSearchEntry = QLineEdit()
        trainerSearchLayout.addWidget(self.trainerSearchEntry)
        self.trainerSearchEntry.setPlaceholderText(self.trainerSearchEntryPrompt)
        self.trainerSearchEntry.textChanged.connect(self.update_list)

        # Display installed trainers
        self.flingListBox = QListWidget()
        self.flingListBox.itemActivated.connect(self.launch_trainer)
        trainersLayout.addWidget(self.flingListBox)

        # Launch and delete buttons
        bottomLayout = QHBoxLayout()
        bottomLayout.setSpacing(6)
        trainersLayout.addLayout(bottomLayout)

        self.launchButton = QPushButton(tr("Launch"))
        bottomLayout.addWidget(self.launchButton)
        self.launchButton.clicked.connect(self.launch_trainer)

        self.deleteButton = QPushButton(tr("Delete"))
        bottomLayout.addWidget(self.deleteButton)
        self.deleteButton.clicked.connect(self.delete_trainer)

        # ===========================================================================
        # Column 2 - downloads
        # ===========================================================================
        downloadsLayout = QVBoxLayout()
        downloadsLayout.setSpacing(10)
        mainLayout.addLayout(downloadsLayout, 0, 1)

        # Search online trainers
        downloadSearchLayout = QHBoxLayout()
        downloadSearchLayout.setSpacing(10)
        downloadSearchLayout.setContentsMargins(20, 0, 20, 0)
        downloadsLayout.addLayout(downloadSearchLayout)

        searchLabel = QLabel()
        searchLabel.setPixmap(QPixmap(self.search_path).scaled(25, 25, Qt.AspectRatioMode.KeepAspectRatio))
        downloadSearchLayout.addWidget(searchLabel)

        self.downloadSearchEntry = QLineEdit()
        self.downloadSearchEntry.setPlaceholderText(self.downloadSearchEntryPrompt)
        self.downloadSearchEntry.returnPressed.connect(self.on_enter_press)
        downloadSearchLayout.addWidget(self.downloadSearchEntry)

        # Display trainer search results
        self.downloadListBox = QListWidget()
        self.downloadListBox.itemActivated.connect(self.on_download_start)
        downloadsLayout.addWidget(self.downloadListBox)

        # Change trainer download path
        changeDownloadPathLayout = QHBoxLayout()
        changeDownloadPathLayout.setSpacing(5)
        downloadsLayout.addLayout(changeDownloadPathLayout)

        self.downloadPathEntry = QLineEdit()
        self.downloadPathEntry.setReadOnly(True)
        self.downloadPathEntry.setText(self.trainerDownloadPath)
        changeDownloadPathLayout.addWidget(self.downloadPathEntry)

        self.fileDialogButton = QPushButton("...")
        changeDownloadPathLayout.addWidget(self.fileDialogButton)
        self.fileDialogButton.clicked.connect(self.change_path)

        self.show_cheats()

        # Show warning pop up
        if settings["showWarning"]:
            dialog = CopyRightWarning(self)
            dialog.show()

        # Update database, trainer update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_main_interval)
        self.on_main_interval()
        self.timer.start(3600000)

    # ===========================================================================
    # Core functions
    # ===========================================================================
    def closeEvent(self, event):
        super().closeEvent(event)
        os._exit(0)

    def init_settings(self):
        if settings["theme"] == "black":
            style = style_sheet.black
        elif settings["theme"] == "white":
            style = style_sheet.white

        style = style.format(
            drop_down_arrow=self.dropDownArrow_path,
            scroll_bar_top=self.upArrow_path,
            scroll_bar_bottom=self.downArrow_path,
            scroll_bar_left=self.leftArrow_path,
            scroll_bar_right=self.rightArrow_path,
        )
        self.setStyleSheet(style)

    def on_enter_press(self):
        keyword = self.downloadSearchEntry.text()
        if keyword and self.searchable:
            self.download_display(keyword)

    def on_download_start(self, item):
        index = self.downloadListBox.row(item)
        if index >= 0 and self.downloadable:
            self.download_trainers(index)

    def disable_download_widgets(self):
        self.downloadSearchEntry.setEnabled(False)
        self.fileDialogButton.setEnabled(False)

    def enable_download_widgets(self):
        self.downloadSearchEntry.setEnabled(True)
        self.fileDialogButton.setEnabled(True)

    def disable_all_widgets(self):
        self.downloadSearchEntry.setEnabled(False)
        self.fileDialogButton.setEnabled(False)
        self.trainerSearchEntry.setEnabled(False)
        self.launchButton.setEnabled(False)
        self.deleteButton.setEnabled(False)

    def enable_all_widgets(self):
        self.downloadSearchEntry.setEnabled(True)
        self.fileDialogButton.setEnabled(True)
        self.trainerSearchEntry.setEnabled(True)
        self.launchButton.setEnabled(True)
        self.deleteButton.setEnabled(True)

    def update_list(self):
        search_text = self.trainerSearchEntry.text().lower()
        if search_text == "":
            self.show_cheats()
            return

        self.flingListBox.clear()
        for trainerName in self.trainers.keys():
            if search_text in trainerName.lower():
                self.flingListBox.addItem(trainerName)

    def show_cheats(self):
        self.flingListBox.clear()
        self.trainers = {}
        entries = sorted(
            os.scandir(self.trainerDownloadPath),
            key=lambda dirent: sort_trainers_key(dirent.name)
        )

        for trainer in entries:
            trainerPath = os.path.normpath(trainer.path)
            trainerName, trainerExt = os.path.splitext(os.path.basename(trainerPath))
            if trainerExt.lower() == ".exe" and os.path.getsize(trainerPath) != 0:
                self.flingListBox.addItem(trainerName)
                self.trainers[trainerName] = trainerPath

    def launch_trainer(self):
        try:
            selection = self.flingListBox.currentRow()
            if selection != -1:
                trainerName = self.flingListBox.item(selection).text()
                os.startfile(os.path.normpath(self.trainers[trainerName]))
        except OSError as e:
            if e.winerror == 1223:
                print("[Launch Trainer] was canceled by the user.")
            else:
                raise

    def delete_trainer(self):
        index = self.flingListBox.currentRow()
        if index != -1:
            trainerName = self.flingListBox.item(index).text()
            trainerPath = self.trainers[trainerName]
        
            msg_box = QMessageBox(
                QMessageBox.Icon.Question,
                tr('Delete trainer'),
                tr('Are you sure you want to delete ') + f"{trainerName}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                self
            )
            
            yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
            yes_button.setText(tr("Confirm"))
            no_button = msg_box.button(QMessageBox.StandardButton.No)
            no_button.setText(tr("Cancel"))
            reply = msg_box.exec()

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    os.chmod(trainerPath, stat.S_IWRITE)
                    os.remove(trainerPath)
                    self.flingListBox.takeItem(index)
                    self.show_cheats()
                except PermissionError as e:
                    QMessageBox.critical(self, tr("Error"), tr("Trainer is currently in use, please close any programs using the file and try again."))
    
    def findWidgetInStatusBar(self, statusbar, widgetName):
        for widget in statusbar.children():
            if widget.objectName() == widgetName:
                return widget
        return None

    def change_path(self):
        self.downloadListBox.clear()
        self.disable_all_widgets()
        folder = QFileDialog.getExistingDirectory(self, tr("Change trainer download path"))

        if folder:
            changedPath = os.path.normpath(os.path.join(folder, "GCM Trainers/"))
            if self.downloadPathEntry.text() == changedPath:
                QMessageBox.critical(self, tr("Error"), tr("Please choose a new path."))
                self.on_message(tr("Failed to change trainer download path."), "failure")
                self.enable_all_widgets()
                return

            self.downloadListBox.addItem(tr("Migrating existing trainers..."))
            migration_thread = PathChangeThread(self.trainerDownloadPath, folder, self)
            migration_thread.finished.connect(self.on_migration_finished)
            migration_thread.error.connect(self.on_migration_error)
            migration_thread.start()
        
        else:
            self.downloadListBox.addItem(tr("No path selected."))
            self.enable_all_widgets()
            return
    
    def download_display(self, keyword):
        self.disable_download_widgets()
        self.downloadListBox.clear()
        self.downloadable = False
        self.searchable = False

        display_thread = DownloadDisplayThread(keyword, self)
        display_thread.message.connect(self.on_message)
        display_thread.finished.connect(self.on_display_finished)
        display_thread.start()
    
    def fetch_database(self):
        if not self.currentlyUpdatingFling:
            self.currentlyUpdatingFling = True
            fetch_fling_site_thread = FetchFlingSite(self)
            fetch_fling_site_thread.message.connect(self.on_status_load)
            fetch_fling_site_thread.update.connect(self.on_status_update)
            fetch_fling_site_thread.finished.connect(self.on_interval_finished)
            fetch_fling_site_thread.start()

        if not self.currentlyUpdatingTrans:
            self.currentlyUpdatingTrans = True
            fetch_trainer_details_thread = FetchTrainerDetails(self)
            fetch_trainer_details_thread.message.connect(self.on_status_load)
            fetch_trainer_details_thread.update.connect(self.on_status_update)
            fetch_trainer_details_thread.finished.connect(self.on_interval_finished)
            fetch_trainer_details_thread.start()
    
    def update_trainers(self):
        if not self.currentlyUpdatingTrainers:
            self.currentlyUpdatingTrainers = True
            trainer_update_thread = UpdateTrainers(self.trainers, self)
            trainer_update_thread.message.connect(self.on_status_load)
            trainer_update_thread.update.connect(self.on_status_update)
            trainer_update_thread.updateTrainer.connect(self.on_trainer_update)
            trainer_update_thread.finished.connect(self.on_interval_finished)
            trainer_update_thread.start()
    
    def on_main_interval(self):
        if settings["autoUpdateDatabase"]:
            self.fetch_database()
        if settings["autoUpdate"]:
            self.update_trainers()

    def download_trainers(self, index):
        self.enqueue_download(index, self.trainers, self.trainerDownloadPath, False, None, None)
    
    def on_trainer_update(self, trainerPath, updateUrl):
        self.enqueue_download(None, None, self.trainerDownloadPath, True, trainerPath, updateUrl)
    
    def enqueue_download(self, index, trainers, trainerDownloadPath, update, trainerPath, updateUrl):
        self.downloadQueue.put((index, trainers, trainerDownloadPath, update, trainerPath, updateUrl))
        if not self.currentlyDownloading:
            self.start_next_download()

    def start_next_download(self):
        if not self.downloadQueue.empty():
            self.currentlyDownloading = True
            self.disable_download_widgets()
            self.downloadListBox.clear()
            self.downloadable = False
            self.searchable = False

            index, trainers, trainerDownloadPath, update, trainerPath, updateUrl = self.downloadQueue.get()
            download_thread = DownloadTrainersThread(index, trainers, trainerDownloadPath, update, trainerPath, updateUrl, self)
            download_thread.message.connect(self.on_message)
            download_thread.messageBox.connect(self.on_message_box)
            download_thread.finished.connect(self.on_download_finished)
            download_thread.start()
        else:
            self.currentlyDownloading = False

    def on_message(self, message, type=None):
        item = QListWidgetItem(message)

        if type == "clear":
            self.downloadListBox.clear()
        elif type == "success":
            # item.setForeground(QColor('green'))
            item.setBackground(QColor(0, 255, 0, 20))
            self.downloadListBox.addItem(item)
        elif type == "failure":
            # item.setForeground(QColor('red'))
            item.setBackground(QColor(255, 0, 0, 20))
            self.downloadListBox.addItem(item)
        else:
            self.downloadListBox.addItem(item)
            
    def on_message_box(self, type, title, text):
        if type == "info":
            QMessageBox.information(self, title, text)
        elif type == "error":
            QMessageBox.critical(self, title, text)
    
    def on_migration_error(self, error_message):
        QMessageBox.critical(self, tr("Error"), tr("Error migrating trainers: ") + error_message)
        self.on_message(tr("Failed to change trainer download path."), "failure")
        self.show_cheats()
        self.enable_all_widgets()
    
    def on_migration_finished(self, new_path):
        self.trainerDownloadPath = new_path
        settings["downloadPath"] = self.trainerDownloadPath
        apply_settings(settings)
        self.show_cheats()
        self.on_message(tr("Migration complete!"), "success")
        self.downloadPathEntry.setText(self.trainerDownloadPath)
        self.enable_all_widgets()

    def on_display_finished(self, status):
        # 0: success; 1: failure
        if status:
            self.downloadable = False
        else:
            self.downloadable = True
            
        self.searchable = True
        self.enable_download_widgets()
    
    def on_download_finished(self, status):
        self.downloadable = False
        self.searchable = True
        self.enable_download_widgets()
        self.show_cheats()
        self.currentlyDownloading = False
        self.start_next_download()

    def on_status_load(self, widgetName, message):
        statusWidget = StatusMessageWidget(widgetName, message)
        self.statusbar.addWidget(statusWidget)

    def on_status_update(self, widgetName, newMessage, state):
        target = self.findWidgetInStatusBar(self.statusbar, widgetName)
        target.update_message(newMessage, state)

    def on_interval_finished(self, widgetName):
        target = self.findWidgetInStatusBar(self.statusbar, widgetName)
        if target:
            target.deleteLater()

        if widgetName == "fling":
            self.currentlyUpdatingFling = False
        elif widgetName == "details":
            self.currentlyUpdatingTrans = False
        elif widgetName == "trainerUpdate":
            self.currentlyUpdatingTrainers = False

    # ===========================================================================
    # Menu functions
    # ===========================================================================
    def open_settings(self):
        if self.settings_window is not None and self.settings_window.isVisible():
            self.settings_window.raise_()
            self.settings_window.activateWindow()
        else:
            self.settings_window = SettingsDialog(self)
            self.settings_window.show()

    def import_files(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, tr("Select trainers you want to import"), "", "Executable Files (*.exe)")
        if file_names:
            for file_name in file_names:
                try:
                    dst = os.path.join(self.trainerDownloadPath, os.path.basename(file_name))
                    if os.path.exists(dst):
                        os.chmod(dst, stat.S_IWRITE)
                    shutil.copy(file_name, dst)
                    print("Trainer copied: ", file_name)
                except Exception as e:
                        QMessageBox.critical(self, tr("Failure"), tr("Failed to import trainer: ") + f"{file_name}\n{str(e)}")
                self.show_cheats()

            msg_box = QMessageBox(
                QMessageBox.Icon.Question,
                tr("Delete original trainers"),
                tr("Do you want to delete the original trainer files?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                self
            )
            
            yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
            yes_button.setText(tr("Yes"))
            no_button = msg_box.button(QMessageBox.StandardButton.No)
            no_button.setText(tr("No"))
            reply = msg_box.exec()

            if reply == QMessageBox.StandardButton.Yes:
                for file_name in file_names:
                    try:
                        os.remove(file_name)
                    except Exception as e:
                        QMessageBox.critical(self, tr("Failure"), tr("Failed to delete original trainer: ") + f"{file_name}\n{str(e)}")

    def open_trainer_directory(self):
        os.startfile(self.trainerDownloadPath)
    
    def add_whitelist(self):
        msg_box = QMessageBox(
            QMessageBox.Icon.Question,
            tr("Administrator Access Required"),
            tr("To proceed with adding the trainer download paths to the Windows Defender whitelist, administrator rights are needed. A User Account Control (UAC) prompt will appear for permission.") +
               "\n\n" + tr("Would you like to continue?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            self
        )
        
        yes_button = msg_box.button(QMessageBox.StandardButton.Yes)
        yes_button.setText(tr("Yes"))
        no_button = msg_box.button(QMessageBox.StandardButton.No)
        no_button.setText(tr("No"))
        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Yes:
            paths = [DOWNLOAD_TEMP_DIR, settings["downloadPath"]]

            try:
                subprocess.run([self.elevator_path] + paths, check=True, shell=True)
                QMessageBox.information(self, tr("Success"), tr("Successfully added paths to Windows Defender whitelist."))

            except subprocess.CalledProcessError:
                QMessageBox.critical(self, tr("Failure"), tr("Failed to add paths to Windows Defender whitelist."))

    def open_about(self):
        if self.about_window is not None and self.about_window.isVisible():
            self.about_window.raise_()
            self.about_window.activateWindow()
        else:
            self.about_window = AboutDialog(self)
            self.about_window.show()

    def wemod_pro(self):
        if self.wemod_window is not None and self.wemod_window.isVisible():
            self.wemod_window.raise_()
            self.wemod_window.activateWindow()
        else:
            self.wemod_window = WeModDialog(self)
            self.wemod_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Language setting
    font_config = {
        "en_US": resource_path("assets/NotoSans-Regular.ttf"),
        "zh_CN": resource_path("assets/NotoSansSC-Regular.ttf"),
        "zh_TW": resource_path("assets/NotoSansTC-Regular.ttf")
    }
    fontId = QFontDatabase.addApplicationFont(
        font_config[settings["language"]])
    fontFamilies = QFontDatabase.applicationFontFamilies(fontId)
    customFont = QFont(fontFamilies[0], 10)
    app.setFont(customFont)

    mainWin = GameCheatsManager()
    mainWin.show()

    # Center window
    qr = mainWin.frameGeometry()
    cp = mainWin.screen().availableGeometry().center()
    qr.moveCenter(cp)
    mainWin.move(qr.topLeft())

    sys.exit(app.exec())
