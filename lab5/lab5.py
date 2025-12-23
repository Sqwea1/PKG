import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np

INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

def compute_code(x, y, xmin, ymin, xmax, ymax):
    code = INSIDE
    if x < xmin: code |= LEFT
    elif x > xmax: code |= RIGHT
    if y < ymin: code |= BOTTOM
    elif y > ymax: code |= TOP
    return code

def cohen_sutherland(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    c1 = compute_code(x1, y1, xmin, ymin, xmax, ymax)
    c2 = compute_code(x2, y2, xmin, ymin, xmax, ymax)

    while True:
        if not (c1 | c2):
            return x1, y1, x2, y2
        if c1 & c2:
            return None

        c = c1 if c1 else c2

        if c & TOP:
            x = x1 + (x2-x1)*(ymax-y1)/(y2-y1)
            y = ymax
        elif c & BOTTOM:
            x = x1 + (x2-x1)*(ymin-y1)/(y2-y1)
            y = ymin
        elif c & RIGHT:
            y = y1 + (y2-y1)*(xmax-x1)/(x2-x1)
            x = xmax
        else:
            y = y1 + (y2-y1)*(xmin-x1)/(x2-x1)
            x = xmin

        if c == c1:
            x1, y1 = x, y
            c1 = compute_code(x1, y1, xmin, ymin, xmax, ymax)
        else:
            x2, y2 = x, y
            c2 = compute_code(x2, y2, xmin, ymin, xmax, ymax)

def is_convex(poly):
    n = len(poly)
    if n < 3:
        return False
    sign = 0
    for i in range(n):
        a = poly[i]
        b = poly[(i+1) % n]
        c = poly[(i+2) % n]
        cross = (b[0]-a[0])*(c[1]-b[1]) - (b[1]-a[1])*(c[0]-b[0])
        if cross != 0:
            if sign == 0:
                sign = 1 if cross > 0 else -1
            elif sign * cross < 0:
                return False
    return True

def fix_ccw(poly):
    area = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i+1) % len(poly)]
        area += (x2 - x1) * (y2 + y1)
    return poly if area < 0 else poly[::-1]

def clip_cyrus_beck(p0, p1, poly):
    poly = fix_ccw(poly)
    d = p1 - p0
    t0, t1 = 0.0, 1.0

    for i in range(len(poly)):
        a = poly[i]
        b = poly[(i+1) % len(poly)]
        edge = b - a
        normal = np.array([-edge[1], edge[0]])
        w = p0 - a

        D = normal @ d
        N = -normal @ w

        if abs(D) < 1e-9:
            if N > 0:
                return None
            continue

        t = N / D
        if D > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)

        if t0 > t1:
            return None

    return p0 + t0*d, p0 + t1*d

class App:
    def __init__(self, root):
        root.title("Отсечение отрезков")
        root.geometry("900x600")

        panel = ttk.Frame(root, padding=10)
        panel.pack(side=tk.LEFT, fill=tk.Y)

        self.txt_segs = tk.Text(panel, width=25, height=10)
        self.txt_segs.insert(tk.END,
            "-12 -4 12 4\n"
            "-6 -3 6 3\n"
            "-5 0 5 0\n"
            "-4 -6 -4 6\n"
            "4 -6 4 6\n"
            "-8 -8 8 8\n"
            "-8 8 8 -8")
        self.txt_segs.pack(pady=5)

        self.txt_poly = tk.Text(panel, width=25, height=8)
        self.txt_poly.insert(tk.END,
            "-6 -2\n"
            "-2 -6\n"
            "4 -4\n"
            "6 0\n"
            "2 6\n"
            "-4 4")
        self.txt_poly.pack(pady=5)

        self.alg = tk.StringVar(value="cyrus")
        ttk.Radiobutton(panel, text="Коэн-Сазерленд", variable=self.alg, value="cohen").pack(anchor="w")
        ttk.Radiobutton(panel, text="Кирус-Бек", variable=self.alg, value="cyrus").pack(anchor="w")
        ttk.Button(panel, text="Построить", command=self.draw).pack(fill=tk.X, pady=10)

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.scale = 20

    def to_screen(self, x, y):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        return w/2 + x*self.scale, h/2 - y*self.scale

    def draw_line(self, x1, y1, x2, y2, color, width=2, dash=None):
        self.canvas.create_line(*self.to_screen(x1,y1), *self.to_screen(x2,y2),
                                fill=color, width=width, dash=dash)

    def draw_poly(self, poly, color):
        pts = []
        for p in poly:
            pts.extend(self.to_screen(p[0], p[1]))
        self.canvas.create_polygon(pts, outline=color, fill='', width=2)

    def draw(self):
        self.canvas.delete("all")

        try:
            segs = [list(map(float, l.split())) for l in self.txt_segs.get("1.0", tk.END).splitlines() if l.strip()]
            poly = np.array([list(map(float, l.split())) for l in self.txt_poly.get("1.0", tk.END).splitlines() if l.strip()])
        except:
            return

        if self.alg.get() == "cyrus" and not is_convex(poly):
            messagebox.showerror("Ошибка", "Полигон невыпуклый")
            return

        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.create_line(0, h/2, w, h/2, fill="#ddd")
        self.canvas.create_line(w/2, 0, w/2, h, fill="#ddd")

        for s in segs:
            self.draw_line(s[0], s[1], s[2], s[3], "gray", 1, (4,4))

        if self.alg.get() == "cohen":
            xmin, ymin = poly.min(axis=0)
            xmax, ymax = poly.max(axis=0)
            self.draw_line(xmin,ymin,xmax,ymin,"red")
            self.draw_line(xmax,ymin,xmax,ymax,"red")
            self.draw_line(xmax,ymax,xmin,ymax,"red")
            self.draw_line(xmin,ymax,xmin,ymin,"red")
            for s in segs:
                r = cohen_sutherland(*s, xmin, ymin, xmax, ymax)
                if r:
                    self.draw_line(*r, "blue", 3)
        else:
            self.draw_poly(poly, "red")
            for s in segs:
                r = clip_cyrus_beck(np.array(s[:2]), np.array(s[2:]), poly)
                if r:
                    self.draw_line(r[0][0], r[0][1], r[1][0], r[1][1], "blue", 3)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
