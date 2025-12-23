import cv2
import numpy as np  
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk

def медианный_фильтр(img):
    return cv2.medianBlur(img, 5)

def фильтр_минимума(img):
    kernel = np.ones((3, 3), np.uint8)
    return cv2.erode(img, kernel)

def фильтр_максимума(img):
    kernel = np.ones((3, 3), np.uint8)
    return cv2.dilate(img, kernel)

def глобальная_пороговая(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)

def пороговая_отсу(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)

def адаптивная_пороговая(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    th = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)

class Приложение:
    def __init__(self, root):
        self.root = root
        self.root.title("Нелинейные фильтры и пороговая обработка")
        self.root.geometry("1000x600")
        self.img = None

        left = ttk.Frame(root, padding=10)
        left.pack(side="left", fill="y")

        ttk.Button(left, text="Загрузить изображение", command=self.load_image).pack(fill="x", pady=5)

        frame = ttk.LabelFrame(left, text="Метод")
        frame.pack(fill="x", pady=10)

        self.method = tk.StringVar(value="Медианный фильтр")

        ttk.Combobox(
            frame,
            state="readonly",
            textvariable=self.method,
            values=[
                "Медианный фильтр",
                "Фильтр минимума",
                "Фильтр максимума",
                "Глобальная пороговая",
                "Пороговая по Отсу",
                "Адаптивная пороговая"
            ]
        ).pack(fill="x", pady=5)

        ttk.Button(frame, text="Применить", command=self.apply).pack(fill="x", pady=5)

        right = ttk.Frame(root, padding=10)
        right.pack(side="right", fill="both", expand=True)

        self.panel_orig = ttk.Label(right, text="Исходное изображение", anchor="center")
        self.panel_orig.pack(side="left", expand=True, padx=10, fill="both")

        self.panel_res = ttk.Label(right, text="Результат", anchor="center")
        self.panel_res.pack(side="right", expand=True, padx=10, fill="both")

    def load_image(self):
        path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not path:
            return

        img = cv2.imread(path)
        if img is None:
            messagebox.showerror("Ошибка", "Не удалось загрузить изображение")
            return

        self.img = img
        self.show(self.img, self.panel_orig)
        self.panel_res.configure(image="", text="Результат")
        self.panel_res.image = None

    def fit_image(self, img, max_w, max_h):
        h, w = img.shape[:2]
        scale = min(max_w / w, max_h / h)
        new_size = (int(w * scale), int(h * scale))
        return cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)

    def show(self, img, panel):
        panel.update_idletasks()
        w = panel.winfo_width()
        h = panel.winfo_height()
        if w < 10 or h < 10:
            w, h = 450, 450

        img = self.fit_image(img, w, h)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(img)

        panel.configure(image=img_tk, text="")
        panel.image = img_tk

    def apply(self):
        if self.img is None:
            messagebox.showwarning("Ошибка", "Сначала загрузите изображение")
            return

        res = self.img.copy()
        m = self.method.get()

        if m == "Медианный фильтр":
            res = медианный_фильтр(res)
        elif m == "Фильтр минимума":
            res = фильтр_минимума(res)
        elif m == "Фильтр максимума":
            res = фильтр_максимума(res)
        elif m == "Глобальная пороговая":
            res = глобальная_пороговая(res)
        elif m == "Пороговая по Отсу":
            res = пороговая_отсу(res)
        elif m == "Адаптивная пороговая":
            res = адаптивная_пороговая(res)

        self.show(res, self.panel_res)

root = tk.Tk()
Приложение(root)
root.mainloop()
