import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import time

IMG_W, IMG_H = 900, 700
BASE_SCALE = 20
MIN_SCALE = 0.01
MAX_SCALE = 100.0

class RasterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Растровые алгоритмы")
        self.geometry("1350x760")

        self.scale = 1.0
        self.algorithm = tk.StringVar(value="dda")

        self.create_ui()
        self.algorithm.trace_add("write", self.update_fields)
        self.update_fields()

    def create_ui(self):
        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        ttk.Label(left, text="Алгоритм").pack(anchor=tk.W)

        algorithms = [
            ("Пошаговый", "step"),
            ("ЦДА", "dda"),
            ("Брезенхем (линия)", "bres_line"),
            ("Брезенхем (окружность)", "bres_circle"),
            ("Кастл-Питвей", "casteljau"),
            ("Ву (сглаживание)", "wu")
        ]

        for t, v in algorithms:
            ttk.Radiobutton(left, text=t, variable=self.algorithm, value=v).pack(anchor=tk.W)

        self.entries = {}
        defaults = {"x0": "-5", "y0": "-5", "x1": "10", "y1": "8", "xc": "0", "yc": "0", "r": "10"}
        
        for lbl in ["x0", "y0", "x1", "y1", "xc", "yc", "r"]:
            ttk.Label(left, text=lbl).pack(anchor=tk.W)
            e = ttk.Entry(left)
            e.insert(0, defaults.get(lbl, "0"))
            e.pack(fill=tk.X)
            self.entries[lbl] = e

        ttk.Button(left, text="Нарисовать", command=self.draw).pack(fill=tk.X, pady=5)
        ttk.Button(left, text="+ Масштаб", command=self.zoom_in).pack(fill=tk.X)
        ttk.Button(left, text="- Масштаб", command=self.zoom_out).pack(fill=tk.X)

        self.time_label = ttk.Label(left, text="Время вычислений: ---")
        self.time_label.pack(pady=5)
        
        self.scale_label = ttk.Label(left, text=f"Масштаб: {self.scale:.2f}x")
        self.scale_label.pack(pady=5)

        self.image_label = ttk.Label(self)
        self.image_label.pack(side=tk.RIGHT, expand=True)

    def update_fields(self, *_):
        required = {
            "step": {"x0", "y0", "x1", "y1"},
            "dda": {"x0", "y0", "x1", "y1"},
            "bres_line": {"x0", "y0", "x1", "y1"},
            "wu": {"x0", "y0", "x1", "y1"},
            "bres_circle": {"xc", "yc", "r"},
            "casteljau": {"x0", "y0", "xc", "yc", "x1", "y1"}
        }

        needed = required[self.algorithm.get()]
        for name, entry in self.entries.items():
            if name in needed:
                entry.configure(state="normal")
            else:
                entry.configure(state="disabled")

    def to_screen(self, x, y):
        ox, oy = IMG_W // 2, IMG_H // 2
        step = int(BASE_SCALE * self.scale)
        return int(ox + x * step), int(oy - y * step)

    def draw_pixel(self, img, x, y):
        cx, cy = self.to_screen(x, y)
        if -100 <= cx <= IMG_W + 100 and -100 <= cy <= IMG_H + 100:
            s = int(BASE_SCALE * self.scale // 2)
            if s < 1: s = 1 
            cv2.rectangle(img, (cx - s, cy - s), (cx + s, cy + s), (0, 0, 0), -1)

    def draw_grid(self, img):
        step_px = int(BASE_SCALE * self.scale)
        if step_px <= 0: step_px = 1
        
        ox, oy = IMG_W // 2, IMG_H // 2

        start_x = (0 - ox) % step_px
        start_y = (0 - oy) % step_px
        
        if step_px > 2:
            for x in range(start_x, IMG_W, step_px):
                cv2.line(img, (x, 0), (x, IMG_H), (220, 220, 220), 1)
            for y in range(start_y, IMG_H, step_px):
                cv2.line(img, (0, y), (IMG_W, y), (220, 220, 220), 1)

        cv2.line(img, (ox, 0), (ox, IMG_H), (0, 0, 0), 2)
        cv2.line(img, (0, oy), (IMG_W, oy), (0, 0, 0), 2)

        cv2.putText(img, "0", (ox + 5, oy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        cv2.putText(img, "X", (IMG_W - 20, oy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        cv2.putText(img, "Y", (ox + 5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        max_logical_x = (IMG_W // 2) // step_px + 1
        max_logical_y = (IMG_H // 2) // step_px + 1
        
        text_step = 1
        if step_px < 5: text_step = 50
        elif step_px < 10: text_step = 20
        elif step_px < 20: text_step = 10
        elif step_px < 40: text_step = 5
        elif step_px < 60: text_step = 2

        for i in range(-int(max_logical_x), int(max_logical_x) + 1):
            if i == 0 or i % text_step != 0: continue
            
            sx, sy = self.to_screen(i, 0)
            cv2.putText(img, str(i), (sx - 5, oy + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

        for i in range(-int(max_logical_y), int(max_logical_y) + 1):
            if i == 0 or i % text_step != 0: continue
            
            sx, sy = self.to_screen(0, i)
            cv2.putText(img, str(i), (ox + 5, sy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

    def step(self, x0, y0, x1, y1):
        pts = []
        if x0 == x1:
            for y in range(min(y0, y1), max(y0, y1) + 1):
                pts.append((x0, y))
            return pts
        k = (y1 - y0) / (x1 - x0)
        b = y0 - k * x0
        for x in range(min(x0, x1), max(x0, x1) + 1):
            pts.append((x, round(k * x + b)))
        return pts

    def dda(self, x0, y0, x1, y1):
        pts = []
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy))
        x, y = x0, y0
        if steps == 0: return [(round(x), round(y))]
        for _ in range(int(steps) + 1):
            pts.append((round(x), round(y)))
            x += dx / steps
            y += dy / steps
        return pts

    def bres_line(self, x0, y0, x1, y1):
        pts = []
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            pts.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return pts

    def bres_circle(self, xc, yc, r):
        pts = []
        x, y = 0, r
        d = 3 - 2 * r
        while y >= x:
            for dx, dy in [(x,y),(-x,y),(x,-y),(-x,-y),(y,x),(-y,x),(y,-x),(-y,-x)]:
                pts.append((xc + dx, yc + dy))
            x += 1
            if d > 0:
                y -= 1
                d += 4 * (x - y) + 10
            else:
                d += 4 * x + 6
        return pts

    def casteljau(self, pts, steps=300):
        res = []
        for i in range(steps + 1):
            t = i / steps
            p = pts.copy()
            while len(p) > 1:
                p = [((1 - t) * p[j][0] + t * p[j+1][0],
                      (1 - t) * p[j][1] + t * p[j+1][1]) for j in range(len(p) - 1)]
            res.append((round(p[0][0]), round(p[0][1])))
        return res

    def wu(self, x0, y0, x1, y1):
        pts = []
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        dx, dy = x1 - x0, y1 - y0
        gradient = dy / dx if dx else 1
        y = y0
        for x in range(int(x0), int(x1) + 1):
            pts.append((int(y), x) if steep else (x, int(y)))
            pts.append((int(y) + 1, x) if steep else (x, int(y) + 1))
            y += gradient
        return pts

    def draw(self):
        img = np.ones((IMG_H, IMG_W, 3), np.uint8) * 255
        self.draw_grid(img)

        try:
            start = time.perf_counter()
            a = self.algorithm.get()

            if a == "bres_circle":
                pts = self.bres_circle(int(self.entries["xc"].get()),
                                       int(self.entries["yc"].get()),
                                       int(self.entries["r"].get()))
            elif a == "casteljau":
                pts = self.casteljau([
                    (int(self.entries["x0"].get()), int(self.entries["y0"].get())),
                    (int(self.entries["xc"].get()), int(self.entries["yc"].get())),
                    (int(self.entries["x1"].get()), int(self.entries["y1"].get()))
                ])
            elif a == "wu":
                pts = self.wu(float(self.entries["x0"].get()),
                              float(self.entries["y0"].get()),
                              float(self.entries["x1"].get()),
                              float(self.entries["y1"].get()))
            else:
                x0 = int(self.entries["x0"].get())
                y0 = int(self.entries["y0"].get())
                x1 = int(self.entries["x1"].get())
                y1 = int(self.entries["y1"].get())
                pts = getattr(self, a)(x0, y0, x1, y1)

            elapsed = (time.perf_counter() - start) * 1000
            self.time_label.config(text=f"Время вычислений: {elapsed:.3f} мс")

            for p in pts:
                self.draw_pixel(img, p[0], p[1])

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            im = ImageTk.PhotoImage(Image.fromarray(rgb))
            self.image_label.configure(image=im)
            self.image_label.image = im

        except ValueError:
            print("Ошибка ввода данных")
        except Exception as e:
            print(f"Ошибка: {e}")

    def zoom_in(self):
        if self.scale * 1.5 <= MAX_SCALE:
            self.scale *= 1.5
            self.scale_label.config(text=f"Масштаб: {self.scale:.2f}x")
            self.draw()

    def zoom_out(self):
        if self.scale / 1.5 >= MIN_SCALE:
            self.scale /= 1.5
            self.scale_label.config(text=f"Масштаб: {self.scale:.2f}x")
            self.draw()

if __name__ == "__main__":
    RasterApp().mainloop()