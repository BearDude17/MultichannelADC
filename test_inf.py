
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QMainWindow,
    QPushButton,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QApplication,

)
import pyqtgraph as pg
y = range(0, 100)
x = range(0, 100)
plt = pg.plot(x, y, pen='r')
plt.setFixedSize(1000, 1000)
plt.showGrid(x=True, y=True)
pg.QtGui.QApplication.exec_()