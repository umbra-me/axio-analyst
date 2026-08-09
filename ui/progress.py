"""Request progress and elapsed-time presentation."""

from typing import Callable

from PySide6 import QtCore, QtWidgets


class RequestProgress(QtCore.QObject):
    def __init__(
        self,
        progress_bar: QtWidgets.QProgressBar,
        status_label: QtWidgets.QLabel,
        elapsed_label: QtWidgets.QLabel,
        is_busy: Callable[[], bool],
        parent: QtCore.QObject,
    ):
        super().__init__(parent)
        self._progress_bar = progress_bar
        self._status_label = status_label
        self._elapsed_label = elapsed_label
        self._is_busy = is_busy
        self._request_clock = QtCore.QElapsedTimer()
        self._elapsed_timer = QtCore.QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._update_elapsed)
        self._generation = 0

    def begin(self, message: str) -> None:
        self._generation += 1
        self._request_clock.start()
        self._elapsed_timer.start()
        self._elapsed_label.setText("0s")
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(5)
        self._progress_bar.show()
        self._status_label.setText(message)

    def update(self, message: str, value: int) -> None:
        if not self._is_busy():
            return
        self._progress_bar.show()
        if value == 40:
            self._progress_bar.setRange(0, 0)
        else:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(value)
        self._status_label.setText(message)

    def finish(self, message: str, completed: bool = False) -> None:
        self._elapsed_timer.stop()
        self._update_elapsed()
        self._status_label.setText(message)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(100 if completed else 0)
        generation = self._generation
        QtCore.QTimer.singleShot(1200, lambda: self._hide_if_idle(generation))

    def stop(self) -> None:
        self._elapsed_timer.stop()

    def _update_elapsed(self) -> None:
        if not self._request_clock.isValid():
            return
        elapsed_seconds = self._request_clock.elapsed() // 1000
        if elapsed_seconds < 60:
            self._elapsed_label.setText(f"{elapsed_seconds}s")
        else:
            minutes, seconds = divmod(elapsed_seconds, 60)
            self._elapsed_label.setText(f"{minutes}m {seconds:02d}s")

    def _hide_if_idle(self, generation: int) -> None:
        if generation == self._generation and not self._is_busy():
            self._progress_bar.hide()
