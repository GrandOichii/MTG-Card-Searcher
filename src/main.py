from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton

import sys
import requests

class CardSearcher(QThread):
    finished = pyqtSignal()
    result = pyqtSignal(list)

    def __init__(self, query):
        super(QThread, self).__init__()
        self.card_name_query = query

    def run(self):
        URL = 'https://api.magicthegathering.io/v1/cards'
        PARAMS = {'name': self.card_name_query}
        r = requests.get(url=URL, params=PARAMS)

        data = r.json()
        card_urls = []
        for card in data['cards']:
            if 'imageUrl' in card:
                card_urls += [card['imageUrl']]
        self.result.emit(card_urls)
        self.finished.emit()

class ImageLoader(QThread):
    finished = pyqtSignal()
    result = pyqtSignal(QImage)

    def __init__(self, imageUrl):
        super(QThread, self).__init__()
        self.imageUrl = imageUrl

    def run(self):
        image = QImage()
        image.loadFromData(requests.get(self.imageUrl).content)
        self.result.emit(image)
        self.finished.emit()


def window():
    app = QApplication([])
    win = MainAppWindow()
    win.show()
    sys.exit(app.exec_())

class MainAppWindow(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        self.setGeometry(0, 0, 400, 620)
        self.setWindowTitle('MTG Card Searcher')
        self.initUI()
        self.show()

    def initUI(self):
        self.card_name = QLineEdit(self)
        self.card_name.setGeometry(2, 2, 300, 30)
        self.card_name.setPlaceholderText('Enter the name of the card')
        
        self.search_cards_button = QPushButton(self)
        self.search_cards_button.setText('Search')
        self.search_cards_button.setGeometry(302, 2, 96, 30)
        self.search_cards_button.clicked.connect(self.search_cards_button_click)

        self.card_image_label = QLabel(self)
        self.card_image_label.setScaledContents(True)
        self.card_image_label.setGeometry(2, 34, 396, 553)
        self.card_image_label.setStyleSheet('border: 1px solid black')

        self.previous_button = QPushButton(self)
        self.previous_button.setText('Previous card')
        self.previous_button.setGeometry(2, 587, 199, 30)
        self.previous_button.setEnabled(False)
        self.previous_button.clicked.connect(self.previous_button_click)

        self.next_button = QPushButton(self)
        self.next_button.setText('Next card')
        self.next_button.setGeometry(203, 587, 199, 30)
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.next_button_click)

    def search_cards_button_click(self):
        if len(self.card_name.text()) == 0:
            self.showMB('Enter the name of the card first', 'MTG Card Searcher')
            return

        self.thread = QThread()
        self.worker = CardSearcher(self.card_name.text())
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.search_cards_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.card_name.setEnabled(False)

        self.worker.result.connect(self.handle_card_urls)

        self.thread.start()

        self.thread.finished.connect(lambda: self.load_image())
        
    def handle_card_urls(self, card_urls):
        self.card_urls = card_urls

        if len(card_urls) == 0:
            self.showMB(f'No cards with name ${self.card_name.text()} found!', 'MTG Card Searcher')
            return
        self.cur_image_id = 0    

    def load_image(self):
        self.thread = QThread()
        self.worker = ImageLoader(self.card_urls[self.cur_image_id])
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)

        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.search_cards_button.setEnabled(False)
        self.previous_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.card_name.setEnabled(False)

        self.worker.result.connect(self.handle_image)

        self.thread.start()
        self.thread.finished.connect(lambda: self.search_cards_button.setEnabled(True))
        self.thread.finished.connect(lambda: self.card_name.setEnabled(True))

    def handle_image(self, image):
        self.card_image_label.setPixmap(QPixmap(image))
        if len(self.card_urls) > 1:
            self.previous_button.setEnabled(True)
            self.next_button.setEnabled(True)   

    def previous_button_click(self):
        self.cur_image_id -= 1
        if self.cur_image_id < 0:
            self.cur_image_id = len(self.card_urls) - 1
        self.load_image()
            
    def next_button_click(self):
        self.cur_image_id += 1
        if self.cur_image_id == len(self.card_urls):
            self.cur_image_id = 0
        self.load_image()

    def showMB(self, text, title):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()




window()