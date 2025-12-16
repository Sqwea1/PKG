import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
import subprocess
import threading
from collections import deque

class ImageInfoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Information Reader")
        self.root.geometry("1100x700")

        self.item_to_path = {}
        self.files_queue = deque()
        self.processing = False
        self.all_files_data = {}

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self.folder_path = tk.StringVar()
        folder_label = tk.Label(top_frame, text="Selected Folder:")
        folder_label.pack(side=tk.LEFT, padx=5)
        folder_entry = tk.Entry(top_frame, textvariable=self.folder_path, width=50, state='readonly')
        folder_entry.pack(side=tk.LEFT, padx=5)
        browse_button = tk.Button(top_frame, text="Browse", command=self.browse_folder)
        browse_button.pack(side=tk.LEFT, padx=5)

        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)

        self.status_label = tk.Label(main_frame, text="Select a folder to begin scanning")
        self.status_label.pack(pady=5)

        content_frame = tk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tk.Label(left_frame, text="Image Files:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        table_frame = tk.Frame(left_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        table_scroll_y = ttk.Scrollbar(table_frame)
        table_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("Filename", "Size (px)", "Resolution (dpi)", "Color Depth", "Compression", "Compression Ratio", "full_path")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                                yscrollcommand=table_scroll_y.set,
                                height=15)

        self.tree.heading("Filename", text="Filename")
        self.tree.heading("Size (px)", text="Size (px)")
        self.tree.heading("Resolution (dpi)", text="Resolution (dpi)")
        self.tree.heading("Color Depth", text="Color Depth")
        self.tree.heading("Compression", text="Compression")
        self.tree.heading("Compression Ratio", text="Compression Ratio")
        self.tree.heading("full_path", text="Full Path")

        self.tree.column("Filename", width=180, minwidth=150)
        self.tree.column("Size (px)", width=100, minwidth=80)
        self.tree.column("Resolution (dpi)", width=120, minwidth=100)
        self.tree.column("Color Depth", width=100, minwidth=80)
        self.tree.column("Compression", width=100, minwidth=80)
        self.tree.column("Compression Ratio", width=120, minwidth=100)
        self.tree.column("full_path", width=0, stretch=False)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        table_scroll_y.config(command=self.tree.yview)

        right_frame = tk.Frame(content_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)

        tk.Label(right_frame, text="Preview:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        preview_container = tk.Frame(right_frame)
        preview_container.pack(fill=tk.BOTH, expand=True, pady=5)

        preview_scroll_x = ttk.Scrollbar(preview_container, orient=tk.HORIZONTAL)
        preview_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.preview_canvas = tk.Canvas(preview_container, bg="white", 
                                      xscrollcommand=preview_scroll_x.set)
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        preview_scroll_x.config(command=self.preview_canvas.xview)

        self.preview_frame = tk.Frame(self.preview_canvas, bg="white")
        self.preview_window = self.preview_canvas.create_window((0, 0), window=self.preview_frame, anchor="nw")

        self.preview_label = tk.Label(self.preview_frame, bg="white")
        self.preview_label.pack(padx=10, pady=10)

        self.preview_frame.bind("<Configure>", self.on_frame_configure)
        self.preview_canvas.bind("<Configure>", self.on_canvas_configure)

        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Double-1>', self.on_double_click)

    def on_frame_configure(self, event):
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.preview_canvas.itemconfig(self.preview_window, width=event.width)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
            self.scan_images()

    def scan_images(self):
        folder = self.folder_path.get()
        if not folder:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_to_path.clear()
        self.all_files_data.clear()

        self.preview_label.config(image='', text="")

        self.processing = True
        self.status_label.config(text="Searching for images...")
        threading.Thread(target=self.process_images, args=(folder,), daemon=True).start()

    def get_color_depth_info(self, img):
        mode_to_bpp = {
            "1": 1,
            "L": 8,
            "P": 8,
            "RGB": 24,
            "RGBA": 32,
            "CMYK": 32,
            "YCbCr": 24,
            "LAB": 24,
            "HSV": 24,
            "I": 32,
            "F": 32,
        }
        bpp = mode_to_bpp.get(img.mode, 0)
        display_str = f"{bpp} bits" if bpp > 0 else "Unknown"
        return display_str, bpp

    def calculate_uncompressed_size(self, width, height, bpp):
        if bpp == 0:
            return 0
        return (width * height * bpp) / 8

    def calculate_compression_ratio(self, compressed_size, uncompressed_size):
        if uncompressed_size == 0 or compressed_size == 0:
            return "—"
        ratio = uncompressed_size / compressed_size
        return f"{ratio:.2f}:1"

    def format_file_size(self, bytes_size):
        if bytes_size == 0:
            return '0 B'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"

    def get_compression_type(self, img, filename):
        ext = os.path.splitext(filename)[1].lower()
        compression_map = {
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.png': 'Deflate (PNG)',
            '.gif': 'LZW (GIF)',
            '.bmp': 'RLE / None (BMP)',
            '.tif': 'TIFF',
            '.tiff': 'TIFF',
            '.pcx': 'RLE (PCX)'
        }
        return compression_map.get(ext, 'Unknown')

    def process_images(self, folder):
        supported_formats = ('.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png', '.pcx')
        image_files = []
        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(supported_formats):
                    image_files.append(os.path.join(root_dir, file))

        total_files = len(image_files)
        if total_files == 0:
            self.root.after(0, lambda: messagebox.showinfo("No Images Found", 
                                 "No supported image files were found in the selected folder."))
            self.root.after(0, self.processing_finished)
            return

        self.root.after(0, lambda: self.progress.config(maximum=total_files, value=0))
        self.root.after(0, lambda: self.status_label.config(text=f"Found {total_files} files. Processing..."))

        for idx, file_path in enumerate(image_files):
            if not self.processing:
                break

            try:
                with Image.open(file_path) as img:
                    filename = os.path.basename(file_path)
                    size_px = f"{img.width} x {img.height}"
                    dpi = img.info.get('dpi', (0, 0))
                    resolution = f"{dpi[0]} x {dpi[1]}" if dpi[0] and dpi[1] else "—"
                    
                    color_depth_str, bpp = self.get_color_depth_info(img)
                    compression_type = self.get_compression_type(img, filename)
                    
                    compressed_size = os.path.getsize(file_path)
                    
                    uncompressed_size = self.calculate_uncompressed_size(img.width, img.height, bpp)
                    compression_ratio = self.calculate_compression_ratio(compressed_size, uncompressed_size)
                    
                    compressed_size_str = self.format_file_size(compressed_size)
                    uncompressed_size_str = self.format_file_size(uncompressed_size)
                    
                    info = {
                        'filename': filename,
                        'size_px': size_px,
                        'resolution': resolution,
                        'color_depth': color_depth_str,
                        'compression': compression_type,
                        'compression_ratio': compression_ratio,
                        'full_path': file_path,
                        'width': img.width,
                        'height': img.height,
                        'file_size': compressed_size_str,
                        'uncompressed_size': uncompressed_size_str,
                        'bpp': bpp
                    }
                    
                    self.files_queue.append(info)
                    self.all_files_data[file_path] = info

                if idx % 50 == 0 or idx == len(image_files) - 1:
                    self.root.after(0, self.update_ui)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

            self.root.after(0, lambda: self.progress.config(value=idx+1))

        self.root.after(0, self.processing_finished)

    def update_ui(self):
        while self.files_queue:
            info = self.files_queue.popleft()
            item_id = self.tree.insert("", tk.END, values=(
                info['filename'],
                info['size_px'],
                info['resolution'],
                info['color_depth'],
                info['compression'],
                info['compression_ratio'],
                info['full_path']
            ))
            self.item_to_path[item_id] = info['full_path']

    def processing_finished(self):
        self.processing = False
        self.status_label.config(text=f"Processing completed. Processed files: {self.progress['value']}")

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        file_path = self.item_to_path.get(item)
        if file_path:
            self.show_preview(file_path)

    def on_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        file_path = self.item_to_path.get(item)
        if file_path:
            try:
                if sys.platform.startswith('win'):
                    os.startfile(file_path)
                elif sys.platform.startswith('darwin'):
                    subprocess.call(['open', file_path])
                elif sys.platform.startswith('linux'):
                    subprocess.call(['xdg-open', file_path])
                else:
                    messagebox.showerror("Error", "Unsupported operating system.")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open file: {e}")

    def show_preview(self, image_path):
        try:
            img = Image.open(image_path)
            
            max_size = 400
            ratio = min(max_size / img.width, max_size / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img_resized)
            
            self.preview_label.config(image=photo)
            self.preview_label.image = photo
            
            info = self.all_files_data.get(image_path, {})
            
            text_lines = [
                f"Size: {info.get('size_px', 'N/A')}",
                f"File: {os.path.basename(image_path)}",
                f"Compression: {info.get('compression', 'N/A')}",
                f"Ratio: {info.get('compression_ratio', 'N/A')}",
                f"File size: {info.get('file_size', 'N/A')}",
                f"Uncompressed: {info.get('uncompressed_size', 'N/A')}"
            ]
            
            self.preview_label.config(text="\n".join(text_lines), 
                                    compound=tk.TOP)
            
        except Exception as e:
            self.preview_label.config(image='', text=f"Error loading:\n{str(e)}")
            print(f"Error loading preview {image_path}: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageInfoApp(root)
    root.mainloop()
