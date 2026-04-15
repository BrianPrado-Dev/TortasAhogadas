import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import sys
from datetime import datetime, date
import win32print
import win32ui
from win32con import *
import copy
import sqlite3
import json
from PIL import Image, ImageTk
import subprocess

# --- VARIABLES GLOBALES ---
ventana_lista_instance = None  # Para controlar ventana única de lista
hora_especifica = None
grupo_actual = None
grupos = []
pedido_actual = []
ventana_sabores = None
label_datos_cliente = None
mensaje_activo = False
plato_counter = 0

# Diccionario de productos (valores iniciales)
menu_productos_default = {
    "Torta": 55,
    "Taco Dorado": 10,
    "Taco Blandito": 25,
    "Refresco": 25,
    "Agua Chica": 15,
    "Agua Grande": 25,
    "Paquete 1": 80,
    "Paquete 2": 85,
    "Caguama": 70,
    "Cerveza": 25,
    "Taco con Carne": 25,
    "Paquete 3": 205,
    "Paquete 4": 320,
    "Paquete 5": 630,
    "Torta Mini": 28
}

# --- UTILIDADES ---
def configurar_consola():
    try:
        if os.name == 'nt':
            os.system('chcp 65001 > nul')
        print("[INIT] Consola configurada correctamente")
    except Exception as e:
        print(f"[WARNING] No se pudo configurar la consola: {e}")

def resolver_ruta(ruta_relativa):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa)

def cargar_icono(ruta_archivo, size=(100, 100)):
    try:
        ruta_real = resolver_ruta(ruta_archivo)
        if not os.path.exists(ruta_real):
            return None
        img_original = Image.open(ruta_real)
        img_resized = img_original.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img_resized)
    except Exception:
        return None

def cargar_precios():
    global menu_productos
    precios_file = "precios.json"
    try:
        if os.path.exists(precios_file):
            with open(precios_file, "r", encoding="utf-8") as f:
                menu_productos = json.load(f)
        else:
            menu_productos = menu_productos_default.copy()
        if "Torta Mini" not in menu_productos:
            menu_productos["Torta Mini"] = 28
    except Exception:
        menu_productos = menu_productos_default.copy()

def guardar_precios():
    try:
        with open("precios.json", "w", encoding="utf-8") as f:
            json.dump(menu_productos, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar los precios: {str(e)}.")

# --- BASE DE DATOS Y LÓGICA DE NEGOCIO ---
menu_productos = {}
cargar_precios()
configurar_consola()

def inicializar_base_datos():
    conn = sqlite3.connect("clientes.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            telefono TEXT PRIMARY KEY,
            domicilio TEXT,
            cruces TEXT
        )
    """)
    conn.commit()
    conn.close()

def buscar_cliente(telefono):
    conn = sqlite3.connect("clientes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT domicilio, cruces FROM clientes WHERE telefono = ?", (telefono,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        entry_domicilio.delete(0, tk.END)
        entry_domicilio.insert(0, resultado[0])
        entry_cruces.delete(0, tk.END)
        entry_cruces.insert(0, resultado[1])
    else:
        entry_domicilio.delete(0, tk.END)
        entry_cruces.delete(0, tk.END)

def guardar_actualizar_cliente(telefono, domicilio, cruces):
    conn = sqlite3.connect("clientes.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO clientes (telefono, domicilio, cruces)
        VALUES (?, ?, ?)
    """, (telefono, domicilio, cruces))
    conn.commit()
    conn.close()

def centrar(texto, ancho=32):
    return texto.center(ancho)

def dividir_texto(texto, ancho_max=32, prefijo="Nota: "):
    if not texto: return ""
    ancho_primera_linea = ancho_max - len(prefijo)
    lineas = []
    palabras = texto.split()
    linea_actual = []
    longitud_actual = 0
    for i, palabra in enumerate(palabras):
        if not lineas: ancho = ancho_primera_linea
        else: ancho = ancho_max
        espacio = 1 if linea_actual else 0
        if longitud_actual + len(palabra) + espacio <= ancho:
            linea_actual.append(palabra)
            longitud_actual += len(palabra) + espacio
        else:
            if linea_actual:
                if not lineas: lineas.append(f"{prefijo}{' '.join(linea_actual)}")
                else:
                    indentacion = " " * len(prefijo)
                    lineas.append(f"{indentacion}{' '.join(linea_actual)}")
            linea_actual = [palabra]
            longitud_actual = len(palabra)
    if linea_actual:
        if not lineas: lineas.append(f"{prefijo}{' '.join(linea_actual)}")
        else:
            indentacion = " " * len(prefijo)
            lineas.append(f"{indentacion}{' '.join(linea_actual)}")
    return "\n".join(lineas)

def dividir_campo(texto, prefijo, ancho_max=32):
    if not texto: return prefijo
    ancho_primera_linea = ancho_max - len(prefijo)
    lineas = []
    palabras = texto.split()
    linea_actual = []
    longitud_actual = 0
    for i, palabra in enumerate(palabras):
        if not lineas: ancho = ancho_primera_linea
        else: ancho = ancho_max
        espacio = 1 if linea_actual else 0
        if longitud_actual + len(palabra) + espacio <= ancho:
            linea_actual.append(palabra)
            longitud_actual += len(palabra) + espacio
        else:
            if linea_actual:
                if not lineas: lineas.append(f"{prefijo}{' '.join(linea_actual)}")
                else:
                    indentacion = " " * len(prefijo)
                    lineas.append(f"{indentacion}{' '.join(linea_actual)}")
            linea_actual = [palabra]
            longitud_actual = len(palabra)
    if linea_actual:
        if not lineas: lineas.append(f"{prefijo}{' '.join(linea_actual)}")
        else:
            indentacion = " " * len(prefijo)
            lineas.append(f"{indentacion}{' '.join(linea_actual)}")
    return "\n".join(lineas)

# --- VENTANAS SELECCION ---
def crear_selector_cantidad(parent, bg="#e6d2a1", valor_inicial=1):
    tk.Label(parent, text="Cantidad de paquetes:", font=("Roboto", 11, "bold"), bg=bg, fg="#3e2723").pack(pady=(6, 2))
    frame_cantidad = tk.Frame(parent, bg=bg)
    frame_cantidad.pack(pady=(0, 10))
    cantidad_entry = tk.Entry(frame_cantidad, font=("Roboto", 14, "bold"), width=4, justify="center")
    cantidad_entry.insert(0, str(max(1, int(valor_inicial))))

    def decrementar():
        try:
            valor = int(cantidad_entry.get())
            if valor > 1:
                cantidad_entry.delete(0, tk.END)
                cantidad_entry.insert(0, str(valor - 1))
        except ValueError:
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, "1")

    def incrementar():
        try:
            valor = int(cantidad_entry.get())
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, str(valor + 1))
        except ValueError:
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, "1")

    tk.Button(frame_cantidad, text="-", font=("Roboto", 12, "bold"), command=decrementar,
              bg="#d32f2f", fg="white", relief="flat", width=3).pack(side="left", padx=6)
    cantidad_entry.pack(side="left", padx=3)
    tk.Button(frame_cantidad, text="+", font=("Roboto", 12, "bold"), command=incrementar,
              bg="#4caf50", fg="white", relief="flat", width=3).pack(side="left", padx=6)
    return cantidad_entry

def leer_cantidad_entry(entry, parent_ventana):
    try:
        cantidad = int(entry.get().strip())
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")
        return cantidad
    except ValueError:
        messagebox.showerror("Error", "Cantidad inválida. Ingresa un número mayor a 0.", parent=parent_ventana)
        return None

def mostrar_ventana_seleccion_carne(callback, cantidad_state=None):
    ventana_carne = tk.Toplevel(ventana)
    ventana_carne.title("Seleccionar Carne")
    ventana_carne.geometry("450x420")
    ventana_carne.configure(bg="#e6d2a1")
    ventana_carne.resizable(False, False)
    selecciones = []
    botones = {}
    tk.Label(ventana_carne, text="Selecciona la carne (Máximo 2)", font=("Roboto", 14, "bold"), bg="#e6d2a1", fg="#3e2723").pack(pady=15)
    frame_botones_carne = tk.Frame(ventana_carne, bg="#e6d2a1")
    frame_botones_carne.pack(pady=10, padx=20, fill="both", expand=True)
    carnes = ["Carne", "Buche", "Lengua", "Mixta"]
    colores_base = ["#d32f2f", "#c62828", "#b71c1c", "#e53935"]
    colores_seleccion = ["#b71c1c", "#a12020", "#901616", "#c02f2f"]
    posiciones = [(0, 0), (0, 1), (1, 0), (1, 1)]
    frame_botones_carne.grid_columnconfigure(0, weight=1)
    frame_botones_carne.grid_columnconfigure(1, weight=1)
    frame_botones_carne.grid_rowconfigure(0, weight=1)
    frame_botones_carne.grid_rowconfigure(1, weight=1)
    def toggle_seleccion(carne, color_base, color_seleccion):
        if carne in selecciones:
            selecciones.remove(carne)
            botones[carne].config(relief="raised", bg=color_base)
        else:
            if len(selecciones) < 2:
                selecciones.append(carne)
                botones[carne].config(relief="sunken", bg=color_seleccion)
            else:
                messagebox.showwarning("Límite alcanzado", "Solo puedes seleccionar un máximo de 2 carnes.", parent=ventana_carne)
    for i, carne in enumerate(carnes):
        pos = posiciones[i]
        color_base = colores_base[i]
        color_seleccion = colores_seleccion[i]
        btn = tk.Button(frame_botones_carne, text=carne, font=("Roboto", 12, "bold"),
                        bg=color_base, fg="white", relief="raised", width=12, height=4,
                        command=lambda c=carne, cb=color_base, cs=color_seleccion: toggle_seleccion(c, cb, cs))
        btn.grid(row=pos[0], column=pos[1], padx=10, pady=10, sticky="nsew")
        botones[carne] = btn
    cantidad_entry = None
    if cantidad_state is not None:
        cantidad_entry = crear_selector_cantidad(ventana_carne, bg="#e6d2a1", valor_inicial=cantidad_state.get("cantidad", 1))

    def on_continuar():
        if not selecciones:
            messagebox.showerror("Error", "Debes seleccionar al menos un tipo de carne.", parent=ventana_carne)
            return
        if cantidad_state is not None and cantidad_entry is not None:
            cantidad = leer_cantidad_entry(cantidad_entry, ventana_carne)
            if cantidad is None:
                return
            cantidad_state["cantidad"] = cantidad
        orden_carnes = {"Carne": 1, "Buche": 2, "Lengua": 3, "Mixta": 4}
        selecciones.sort(key=lambda x: orden_carnes[x])
        resultado = "-".join(selecciones)
        ventana_carne.destroy()
        callback(resultado)
    btn_continuar = tk.Button(ventana_carne, text="Continuar", font=("Roboto", 13, "bold"),
                              bg="#4caf50", fg="white", command=on_continuar, pady=8)
    btn_continuar.pack(pady=12, padx=20, fill="x")
    ventana_carne.transient(ventana)
    ventana_carne.grab_set()
    ventana.wait_window(ventana_carne)

def mostrar_ventana_tipo_taco(callback, cantidad_state=None):
    ventana_taco = tk.Toplevel(ventana)
    ventana_taco.title("Seleccionar Tipo de Taco")
    ventana_taco.geometry("450x420")
    ventana_taco.configure(bg="#e6d2a1")
    ventana_taco.resizable(False, False)
    selecciones = []
    botones = {}
    tk.Label(ventana_taco, text="Selecciona el tipo de taco", font=("Roboto", 14, "bold"), bg="#e6d2a1", fg="#3e2723").pack(pady=15)
    frame_botones_taco = tk.Frame(ventana_taco, bg="#e6d2a1")
    frame_botones_taco.pack(pady=10, padx=20, fill="both", expand=True)
    tipos = ["Papa", "Frijol", "Requeson", "Picadillo"]
    colores_base = {"Papa": "#FFF59D", "Frijol": "#8D6E63", "Requeson": "#EEEEEE", "Picadillo": "#BF360C"}
    colores_seleccion = {"Papa": "#FBC02D", "Frijol": "#5D4037", "Requeson": "#BDBDBD", "Picadillo": "#9E2B0C"}
    text_colors = {"Papa": "black", "Frijol": "white", "Requeson": "black", "Picadillo": "white"}
    posiciones = [(0, 0), (0, 1), (1, 0), (1, 1)]
    frame_botones_taco.grid_columnconfigure(0, weight=1)
    frame_botones_taco.grid_columnconfigure(1, weight=1)
    frame_botones_taco.grid_rowconfigure(0, weight=1)
    frame_botones_taco.grid_rowconfigure(1, weight=1)
    def toggle_seleccion(tipo):
        color_base = colores_base[tipo]
        color_seleccion = colores_seleccion[tipo]
        if tipo in selecciones:
            selecciones.remove(tipo)
            botones[tipo].config(relief="raised", bg=color_base)
        else:
            selecciones.append(tipo)
            botones[tipo].config(relief="sunken", bg=color_seleccion)
    for i, tipo in enumerate(tipos):
        pos = posiciones[i]
        btn = tk.Button(frame_botones_taco, text=tipo, font=("Roboto", 12, "bold"),
                        bg=colores_base[tipo], fg=text_colors[tipo], relief="raised", width=12, height=4,
                        command=lambda t=tipo: toggle_seleccion(t))
        btn.grid(row=pos[0], column=pos[1], padx=10, pady=10, sticky="nsew")
        botones[tipo] = btn
    cantidad_entry = None
    if cantidad_state is not None:
        cantidad_entry = crear_selector_cantidad(ventana_taco, bg="#e6d2a1", valor_inicial=cantidad_state.get("cantidad", 1))

    def on_continuar():
        if not selecciones:
            messagebox.showerror("Error", "Debes seleccionar al menos un tipo de taco.", parent=ventana_taco)
            return
        if cantidad_state is not None and cantidad_entry is not None:
            cantidad = leer_cantidad_entry(cantidad_entry, ventana_taco)
            if cantidad is None:
                return
            cantidad_state["cantidad"] = cantidad
        orden_tipos = {"Papa": 1, "Frijol": 2, "Requeson": 3, "Picadillo": 4}
        selecciones.sort(key=lambda x: orden_tipos[x])
        resultado = "-".join(selecciones)
        ventana_taco.destroy()
        callback(resultado)
    btn_continuar = tk.Button(ventana_taco, text="Continuar", font=("Roboto", 13, "bold"),
                              bg="#4caf50", fg="white", command=on_continuar, pady=8)
    btn_continuar.pack(pady=12, padx=20, fill="x")
    ventana_taco.transient(ventana)
    ventana_taco.grab_set()
    ventana.wait_window(ventana_taco)

def mostrar_ventana_sabores(nombre, callback=None):
    global ventana_sabores
    if ventana_sabores: ventana_sabores.destroy()
    ventana_sabores = tk.Toplevel(ventana)
    ventana_sabores.title("Seleccionar Sabor")
    window_width = max(int(screen_width * 0.35), 400)
    window_height = max(int(screen_height * 0.35), 300)
    ventana_sabores.geometry(f"{window_width}x{window_height}")
    ventana_sabores.configure(bg="#e6d2a1")
    ventana_sabores.resizable(True, True)
    ventana_sabores.minsize(400, 300)
    tk.Label(ventana_sabores, text=f"Selecciona el sabor para {nombre}", font=("Roboto", 14, "bold"), bg="#e6d2a1", fg="#3e2723").pack(pady=20, fill="x")
    frame_btn_sabores = tk.Frame(ventana_sabores, bg="#e6d2a1")
    frame_btn_sabores.pack(pady=20, fill="both", expand=True, padx=30)
    frame_btn_sabores.grid_columnconfigure(0, weight=1)
    frame_btn_sabores.grid_columnconfigure(1, weight=1)
    frame_btn_sabores.grid_rowconfigure(0, weight=1)
    btn_jamaica = tk.Button(frame_btn_sabores, text="JAMAICA", font=("Roboto", 14, "bold"),
                            bg="#9c0000", fg="white", relief="flat", activebackground="#7a0000",
                            command=lambda: [callback("Jamaica") if callback else agregar_producto(nombre, "Jamaica"), ventana_sabores.destroy()])
    btn_jamaica.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
    btn_jamaica.bind("<Enter>", lambda e: btn_jamaica.config(bg="#7a0000"))
    btn_jamaica.bind("<Leave>", lambda e: btn_jamaica.config(bg="#9c0000"))
    btn_horchata = tk.Button(frame_btn_sabores, text="HORCHATA", font=("Roboto", 14, "bold"),
                             bg="#ffffff", fg="black", relief="flat", activebackground="#a8a4a4",
                             command=lambda: [callback("Horchata") if callback else agregar_producto(nombre, "Horchata"), ventana_sabores.destroy()])
    btn_horchata.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
    btn_horchata.bind("<Enter>", lambda e: btn_horchata.config(bg="#a8a4a4"))
    btn_horchata.bind("<Leave>", lambda e: btn_horchata.config(bg="#ffffff"))
    frame_btn_sabores.grid_rowconfigure(0, weight=1, minsize=120)
    frame_btn_sabores.grid_columnconfigure(0, weight=1, minsize=120)
    frame_btn_sabores.grid_columnconfigure(1, weight=1, minsize=120)
    ventana_sabores.protocol("WM_DELETE_WINDOW", lambda: ventana_sabores.destroy())

def mostrar_ventana_refrescos(nombre, callback=None):
    global ventana_sabores
    if ventana_sabores:
        ventana_sabores.destroy()

    ventana_sabores = tk.Toplevel(ventana)
    ventana_sabores.title("Seleccionar Refresco")
    window_width = max(int(screen_width * 0.45), 500)
    window_height = max(int(screen_height * 0.4), 350)
    ventana_sabores.geometry(f"{window_width}x{window_height}")
    ventana_sabores.configure(bg="#e6d2a1")
    ventana_sabores.resizable(True, True)

    tk.Label(ventana_sabores, text=f"Selecciona el tipo de {nombre}",
             font=("Roboto", 14, "bold"), bg="#e6d2a1", fg="#3e2723").pack(pady=15, fill="x")

    frame_btn_refrescos = tk.Frame(ventana_sabores, bg="#e6d2a1")
    frame_btn_refrescos.pack(pady=10, fill="both", expand=True, padx=20)

    frame_btn_refrescos.grid_columnconfigure(0, weight=1)
    frame_btn_refrescos.grid_columnconfigure(1, weight=1)
    frame_btn_refrescos.grid_rowconfigure(0, weight=1)
    frame_btn_refrescos.grid_rowconfigure(1, weight=1)
    frame_btn_refrescos.grid_rowconfigure(2, weight=1) 

    # --- CARGAR IMÁGENES ---
    img_coca = cargar_icono("coca.png", size=(100, 100)) 
    img_fanta = cargar_icono("fanta.png", size=(100, 100))
    img_mundet = cargar_icono("mundet.png", size=(100, 100))
    img_sprite = cargar_icono("sprite.png", size=(100, 100))
    img_coca_light = cargar_icono("cocalight.png", size=(100, 100))

    # --- CONFIGURACIÓN DE BOTONES ---
    btn_coca = tk.Button(frame_btn_refrescos, bg="#d32f2f", activebackground="#b71c1c",
                         image=img_coca if img_coca else None, text="" if img_coca else "COCA",
                         command=lambda: [callback("COCA") if callback else agregar_producto(nombre, "COCA"), ventana_sabores.destroy()])
    if img_coca: btn_coca.image = img_coca 
    btn_coca.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
    btn_coca.bind("<Enter>", lambda e: btn_coca.config(bg="#b71c1c"))
    btn_coca.bind("<Leave>", lambda e: btn_coca.config(bg="#d32f2f"))

    btn_fanta = tk.Button(frame_btn_refrescos, bg="#ff6f00", activebackground="#ef6c00",
                          image=img_fanta if img_fanta else None, text="" if img_fanta else "FANTA",
                          command=lambda: [callback("FANTA") if callback else agregar_producto(nombre, "FANTA"), ventana_sabores.destroy()])
    if img_fanta: btn_fanta.image = img_fanta
    btn_fanta.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
    btn_fanta.bind("<Enter>", lambda e: btn_fanta.config(bg="#ef6c00"))
    btn_fanta.bind("<Leave>", lambda e: btn_fanta.config(bg="#ff6f00"))

    btn_mundet = tk.Button(frame_btn_refrescos, bg="#8d6e63", activebackground="#6d4c41",
                          image=img_mundet if img_mundet else None, text="" if img_mundet else "MANZA",
                          command=lambda: [callback("MANZA") if callback else agregar_producto(nombre, "MANZA"), ventana_sabores.destroy()])
    if img_mundet: btn_mundet.image = img_mundet
    btn_mundet.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
    btn_mundet.bind("<Enter>", lambda e: btn_mundet.config(bg="#6d4c41"))
    btn_mundet.bind("<Leave>", lambda e: btn_mundet.config(bg="#8d6e63"))

    btn_sprite = tk.Button(frame_btn_refrescos, bg="#4caf50", activebackground="#388e3c",
                           image=img_sprite if img_sprite else None, text="" if img_sprite else "SPRITE",
                           command=lambda: [callback("SPRITE") if callback else agregar_producto(nombre, "SPRITE"), ventana_sabores.destroy()])
    if img_sprite: btn_sprite.image = img_sprite
    btn_sprite.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")
    btn_sprite.bind("<Enter>", lambda e: btn_sprite.config(bg="#388e3c"))
    btn_sprite.bind("<Leave>", lambda e: btn_sprite.config(bg="#4caf50"))

    btn_coca_light = tk.Button(frame_btn_refrescos, bg="#424242", activebackground="#212121",
                           image=img_coca_light if img_coca_light else None, text="" if img_coca_light else "COCA LIGHT",
                           command=lambda: [callback("COCA LIGHT") if callback else agregar_producto(nombre, "COCA LIGHT"), ventana_sabores.destroy()])
    if img_coca_light: btn_coca_light.image = img_coca_light
    btn_coca_light.grid(row=2, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
    btn_coca_light.bind("<Enter>", lambda e: btn_coca_light.config(bg="#212121"))
    btn_coca_light.bind("<Leave>", lambda e: btn_coca_light.config(bg="#424242"))

    ventana_sabores.protocol("WM_DELETE_WINDOW", lambda: ventana_sabores.destroy())

def mostrar_ventana_item_unificado(nombre, tipo_variante=None):
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos: grupos.append("General")
    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({ "nombre": "Envío", "anotacion": None, "precio": 15, "grupo": "General", "cantidad": 1 })

    ventana_item = tk.Toplevel(ventana)
    ventana_item.title(f"Agregar {nombre}")
    if tipo_variante == "carne_taco":
        ventana_item.geometry("820x660")
    elif tipo_variante == "carne":
        ventana_item.geometry("620x640")
    else:
        ventana_item.geometry("620x700")
    ventana_item.configure(bg="#e6d2a1")
    ventana_item.resizable(False, False)

    tk.Label(ventana_item, text=f"{nombre}", font=("Roboto", 14, "bold"), bg="#e6d2a1", fg="#3e2723").pack(pady=(12, 8))

    carnes_sel = []
    tacos_sel = []
    bebida_sel = tk.StringVar(value="")

    def obtener_carnes():
        if not carnes_sel:
            return None
        orden_carnes = {"Carne": 1, "Buche": 2, "Lengua": 3, "Mixta": 4}
        return "-".join(sorted(carnes_sel, key=lambda x: orden_carnes[x]))

    def obtener_tacos():
        if not tacos_sel:
            return None
        orden_tacos = {"Papa": 1, "Frijol": 2, "Requeson": 3, "Picadillo": 4}
        return "-".join(sorted(tacos_sel, key=lambda x: orden_tacos[x]))

    def crear_selector_carnes(parent, titulo="Selecciona carne (máximo 2):"):
        seccion = tk.LabelFrame(parent, text=titulo, font=("Roboto", 11, "bold"), bg="#f3e8c2", fg="#3e2723", bd=2, relief="groove", padx=10, pady=8)
        if tipo_variante == "carne":
            seccion.pack(fill="x", expand=False, padx=8, pady=6)
        else:
            seccion.pack(fill="both", expand=True, padx=8, pady=6)
        frame = tk.Frame(seccion, bg="#f3e8c2")
        frame.pack(fill="x", expand=False)
        botones = {}
        config = [("Carne", "#d32f2f", "#b71c1c"), ("Buche", "#c62828", "#a12020"), ("Lengua", "#b71c1c", "#901616"), ("Mixta", "#e53935", "#c02f2f")]
        if tipo_variante == "carne":
            btn_w = 17
            btn_h = 5
            btn_font = ("Roboto", 13, "bold")
        elif tipo_variante == "carne_taco":
            btn_w = 16
            btn_h = 4
            btn_font = ("Roboto", 12, "bold")
        else:
            btn_w = 15
            btn_h = 4
            btn_font = ("Roboto", 12, "bold")
        for i, (txt, cbase, csel) in enumerate(config):
            btn = tk.Button(frame, text=txt, font=btn_font, bg=cbase, fg="white", relief="raised", width=btn_w, height=btn_h)
            def on_click(valor=txt, base=cbase, sel=csel):
                if valor in carnes_sel:
                    carnes_sel.remove(valor)
                    botones[valor].config(bg=base, relief="raised")
                else:
                    if len(carnes_sel) >= 2:
                        messagebox.showwarning("Límite", "Máximo 2 carnes.", parent=ventana_item)
                        return
                    carnes_sel.append(valor)
                    botones[valor].config(bg=sel, relief="sunken")
            btn.config(command=on_click)
            btn.grid(row=i // 2, column=i % 2, padx=8, pady=8)
            botones[txt] = btn

    def crear_selector_tacos(parent, titulo="Selecciona tipo de taco:"):
        seccion = tk.LabelFrame(parent, text=titulo, font=("Roboto", 11, "bold"), bg="#f3e8c2", fg="#3e2723", bd=2, relief="groove", padx=10, pady=8)
        if tipo_variante == "taco":
            seccion.pack(fill="x", expand=False, padx=8, pady=6)
        else:
            seccion.pack(fill="both", expand=True, padx=8, pady=6)
        frame = tk.Frame(seccion, bg="#f3e8c2")
        frame.pack(fill="x", expand=False)
        botones = {}
        config = [("Papa", "#FFF59D", "#FBC02D", "black"), ("Frijol", "#8D6E63", "#5D4037", "white"),
                  ("Requeson", "#EEEEEE", "#BDBDBD", "black"), ("Picadillo", "#BF360C", "#9E2B0C", "white")]
        for i, (txt, cbase, csel, fg) in enumerate(config):
            if tipo_variante == "taco":
                btn = tk.Button(frame, text=txt, font=("Roboto", 13, "bold"), bg=cbase, fg=fg, relief="raised", width=17, height=5)
            else:
                btn = tk.Button(frame, text=txt, font=("Roboto", 12, "bold"), bg=cbase, fg=fg, relief="raised", width=13, height=4)
            def on_click(valor=txt, base=cbase, sel=csel):
                if valor in tacos_sel:
                    tacos_sel.remove(valor)
                    botones[valor].config(bg=base, relief="raised")
                else:
                    tacos_sel.append(valor)
                    botones[valor].config(bg=sel, relief="sunken")
            btn.config(command=on_click)
            btn.grid(row=i // 2, column=i % 2, padx=8, pady=8)
            botones[txt] = btn

    def crear_selector_refresco(parent):
        tk.Label(parent, text="Selecciona refresco:", font=("Roboto", 11, "bold"), bg="#e6d2a1", fg="#3e2723").pack(anchor="w", pady=(4, 4))
        frame = tk.Frame(parent, bg="#e6d2a1")
        frame.pack(pady=(0, 4))
        opciones = [("COCA", "#d32f2f"), ("FANTA", "#ff6f00"), ("MANZA", "#8d6e63"), ("SPRITE", "#4caf50"), ("COCA LIGHT", "#424242")]
        for i, (txt, color) in enumerate(opciones):
            fg = "black" if txt == "COCA LIGHT" else "white"
            rb = tk.Radiobutton(frame, text=txt, value=txt, variable=bebida_sel, indicatoron=0,
                                font=("Roboto", 11, "bold"), bg=color, fg=fg, selectcolor=color,
                                activebackground=color, activeforeground=fg, relief="flat", width=12, height=4)
            rb.grid(row=i // 2, column=i % 2, padx=8, pady=8)

    def crear_selector_agua(parent):
        tk.Label(parent, text="Selecciona agua fresca:", font=("Roboto", 11, "bold"), bg="#e6d2a1", fg="#3e2723").pack(anchor="w", pady=(4, 4))
        frame = tk.Frame(parent, bg="#e6d2a1")
        frame.pack(pady=(0, 4))
        opciones = [("Jamaica", "#9c0000", "white"), ("Horchata", "#f5f5f5", "black")]
        for i, (txt, color, fg) in enumerate(opciones):
            rb = tk.Radiobutton(frame, text=txt, value=txt, variable=bebida_sel, indicatoron=0,
                                font=("Roboto", 11, "bold"), bg=color, fg=fg, selectcolor=color,
                                activebackground=color, activeforeground=fg, relief="flat", width=12, height=4)
            rb.grid(row=0, column=i, padx=8, pady=8)

    frame_variante = tk.Frame(ventana_item, bg="#e6d2a1")
    if tipo_variante == "carne":
        frame_variante.pack(fill="x", expand=False, padx=12, pady=(2, 0))
    else:
        frame_variante.pack(fill="both", expand=True, padx=12, pady=(2, 0))

    if tipo_variante == "carne_taco":
        frame_variante.grid_columnconfigure(0, weight=1, uniform="seccion_variante")
        frame_variante.grid_columnconfigure(1, weight=1, uniform="seccion_variante")
        frame_izq = tk.Frame(frame_variante, bg="#e6d2a1")
        frame_der = tk.Frame(frame_variante, bg="#e6d2a1")
        frame_izq.grid(row=0, column=0, sticky="nsew")
        frame_der.grid(row=0, column=1, sticky="nsew")
        crear_selector_carnes(frame_izq, "Sección Carne")
        crear_selector_tacos(frame_der, "Sección Sabor de Taco")
    else:
        if tipo_variante == "carne":
            crear_selector_carnes(frame_variante)
        if tipo_variante == "taco":
            crear_selector_tacos(frame_variante)
        if tipo_variante == "refresco":
            crear_selector_refresco(frame_variante)
        if tipo_variante == "agua":
            crear_selector_agua(frame_variante)

    if tipo_variante in ("carne", "taco"):
        frame_variante.update_idletasks()
        requerido = frame_variante.winfo_reqheight() + 220
        nuevo_alto = max(640, min(requerido, 760))
        ventana_item.geometry(f"620x{nuevo_alto}")

    tk.Label(ventana_item, text="Cantidad:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=(10, 2))
    frame_cantidad = tk.Frame(ventana_item, bg="#e6d2a1")
    frame_cantidad.pack(pady=5)
    font_widgets = ("Roboto", 16, "bold")
    cantidad_entry = tk.Entry(frame_cantidad, font=font_widgets, width=5, justify='center')
    cantidad_entry.insert(0, "1")

    def decrementar_cantidad():
        try:
            valor_actual = int(cantidad_entry.get())
            if valor_actual > 1:
                cantidad_entry.delete(0, tk.END)
                cantidad_entry.insert(0, str(valor_actual - 1))
        except ValueError:
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, "1")

    def incrementar_cantidad():
        try:
            valor_actual = int(cantidad_entry.get())
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, str(valor_actual + 1))
        except ValueError:
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, "1")

    tk.Button(frame_cantidad, text="-", font=font_widgets, command=decrementar_cantidad, bg="#d32f2f", fg="white", relief="flat").pack(side=tk.LEFT, padx=10)
    cantidad_entry.pack(side=tk.LEFT, padx=5)
    tk.Button(frame_cantidad, text="+", font=font_widgets, command=incrementar_cantidad, bg="#4CAF50", fg="white", relief="flat").pack(side=tk.LEFT, padx=10)

    tk.Label(ventana_item, text="Nota:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=8)
    nota_entry = tk.Entry(ventana_item, font=("Roboto", 12), width=32)
    nota_entry.pack(pady=8)

    def confirmar():
        try:
            cantidad = int(cantidad_entry.get())
            if cantidad <= 0:
                raise ValueError("Cantidad debe ser mayor a 0.")

            variante = None
            if tipo_variante == "carne":
                variante = obtener_carnes()
                if not variante:
                    messagebox.showerror("Error", "Selecciona al menos una carne.", parent=ventana_item)
                    return
            elif tipo_variante == "taco":
                variante = obtener_tacos()
                if not variante:
                    messagebox.showerror("Error", "Selecciona al menos un tipo de taco.", parent=ventana_item)
                    return
            elif tipo_variante == "carne_taco":
                carne = obtener_carnes()
                taco = obtener_tacos()
                if not carne or not taco:
                    messagebox.showerror("Error", "Selecciona carne y tipo de taco.", parent=ventana_item)
                    return
                variante = f"{carne}, {taco}"
            elif tipo_variante in ("refresco", "agua"):
                variante = bebida_sel.get().strip()
                if not variante:
                    messagebox.showerror("Error", "Selecciona una bebida.", parent=ventana_item)
                    return

            nota = nota_entry.get().strip()
            if variante and nota:
                anotacion_final = f"{variante}, {nota}"
            elif variante:
                anotacion_final = variante
            elif nota:
                anotacion_final = nota
            else:
                anotacion_final = None

            precio_final = menu_productos[nombre] * cantidad
            item = { "nombre": nombre, "anotacion": anotacion_final, "precio": precio_final, "grupo": grupo_actual, "cantidad": cantidad }
            pedido_actual.append(item)
            ventana_item.destroy()
            actualizar_ticket()
        except ValueError as e:
            messagebox.showerror("Error", f"Entrada inválida: {e}", parent=ventana_item)

    tk.Button(ventana_item, text="Confirmar", font=("Roboto", 12, "bold"), bg="#4caf50", fg="white", command=confirmar, width=18, pady=6).pack(pady=12)
    ventana_item.transient(ventana)

def mostrar_ventana_bebida_paquete(nombre_paquete, seleccion_carne, seleccion_taco, cantidad_state=None):
    global ventana_sabores
    if ventana_sabores: ventana_sabores.destroy()
    ventana_sabores = tk.Toplevel(ventana)
    ventana_sabores.title(f"Seleccionar Bebida para {nombre_paquete}")
    window_width = max(int(screen_width * 0.7), 860)
    window_height = max(int(screen_height * 0.62), 520)
    ventana_sabores.geometry(f"{window_width}x{window_height}")
    ventana_sabores.configure(bg="#e6d2a1")
    ventana_sabores.resizable(True, True)
    ventana_sabores.minsize(860, 520)

    tk.Label(
        ventana_sabores,
        text=f"Selecciona la bebida para {nombre_paquete}",
        font=("Roboto", 14, "bold"),
        bg="#e6d2a1",
        fg="#3e2723"
    ).pack(pady=(12, 2), fill="x")
    tk.Label(
        ventana_sabores,
        text="Toca una opción para agregarla al paquete",
        font=("Roboto", 10),
        bg="#e6d2a1",
        fg="#6d4c41"
    ).pack(pady=(0, 10), fill="x")

    frame_btn_bebidas = tk.Frame(ventana_sabores, bg="#e6d2a1")
    frame_btn_bebidas.pack(pady=4, fill="both", expand=True, padx=16)
    for c in range(3):
        frame_btn_bebidas.grid_columnconfigure(c, weight=1, uniform="seccion_bebida")

    cantidad_entry = crear_selector_cantidad(
        ventana_sabores,
        bg="#e6d2a1",
        valor_inicial=cantidad_state.get("cantidad", 1) if cantidad_state else 1
    )

    secciones_bebida = [
        ("Refrescos", "#0288d1", [
            ("COCA", "#d32f2f", "#b71c1c", "refresco", 0),
            ("FANTA", "#ff6f00", "#ef6c00", "refresco", 0),
            ("MANZA", "#8d6e63", "#6d4c41", "refresco", 0),
            ("SPRITE", "#4caf50", "#388e3c", "refresco", 0),
            ("COCA LIGHT", "#424242", "#212121", "refresco", 0),
        ]),
        ("Aguas frescas", "#43a047", [
            ("JAMAICA", "#9c0000", "#7a0000", "agua", 0),
            ("HORCHATA", "#f5f5f5", "#d6d6d6", "agua", 0),
        ]),
        ("Corona (+$5)", "#bf8c00", [
            ("CORONA CLARA (+$5)", "#f9a825", "#f57f17", "cerveza", 5),
            ("CORONA OSCURA (+$5)", "#5d4037", "#4e342e", "cerveza", 5),
        ]),
    ]

    def seleccionar_bebida_paquete(texto_boton, categoria="refresco", extra_precio=0):
        cantidad_final = 1
        if cantidad_entry is not None:
            cantidad_leida = leer_cantidad_entry(cantidad_entry, ventana_sabores)
            if cantidad_leida is None:
                return
            cantidad_final = cantidad_leida
            if cantidad_state is not None:
                cantidad_state["cantidad"] = cantidad_final
        if texto_boton.startswith("CORONA CLARA"):
            bebida = "Corona Clara"
        elif texto_boton.startswith("CORONA OSCURA"):
            bebida = "Corona Oscura"
        else:
            bebida = texto_boton

        if categoria == "agua":
            anotacion = f"Agua: {bebida.title()}, Torta({seleccion_carne}), Tacos({seleccion_taco})"
        elif categoria == "cerveza":
            anotacion = f"Cerveza: {bebida.title()}, Torta({seleccion_carne}), Tacos({seleccion_taco})"
        else:
            anotacion = f"Refresco: {bebida}, Torta({seleccion_carne}), Tacos({seleccion_taco})"

        ventana_sabores.destroy()
        agregar_producto_paquete_bebida(nombre_paquete, anotacion, extra_precio, cantidad_predeterminada=cantidad_final)

    for idx, (titulo, color_titulo, opciones) in enumerate(secciones_bebida):
        frame_seccion = tk.Frame(frame_btn_bebidas, bg="#f7efd8", bd=1, relief="solid")
        frame_seccion.grid(row=0, column=idx, padx=6, pady=4, sticky="nsew")

        header_seccion = tk.Frame(frame_seccion, bg=color_titulo, height=28)
        header_seccion.pack(fill="x")
        header_seccion.pack_propagate(False)
        tk.Label(
            header_seccion,
            text=titulo,
            font=("Roboto", 10, "bold"),
            bg=color_titulo,
            fg="white"
        ).pack(anchor="w", padx=8, pady=4)

        grid_seccion = tk.Frame(frame_seccion, bg="#f7efd8")
        grid_seccion.pack(fill="both", expand=True, padx=8, pady=8)
        grid_seccion.grid_columnconfigure(0, weight=1)

        for i, (texto, color, hover, categoria, extra) in enumerate(opciones):
            fg_color = "black" if texto == "HORCHATA" else "white"
            btn = tk.Button(
                grid_seccion,
                text=texto,
                font=("Roboto", 10, "bold"),
                bg=color,
                fg=fg_color,
                relief="flat",
                activebackground=hover,
                width=13,
                height=4,
                command=lambda t=texto, cat=categoria, e=extra: seleccionar_bebida_paquete(t, cat, e)
            )
            btn.grid(row=i, column=0, padx=5, pady=5, sticky="nsew")
            btn.bind("<Enter>", lambda e, b=btn, c=hover: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))

    tk.Label(
        ventana_sabores,
        text="* Corona clara y oscura agregan $5 al paquete",
        font=("Roboto", 9, "italic"),
        bg="#e6d2a1",
        fg="#6d4c41"
    ).pack(pady=(4, 8))
    ventana_sabores.protocol("WM_DELETE_WINDOW", lambda: ventana_sabores.destroy())

def seleccionar_refresco_paquete(nombre_paquete, seleccion_carne, seleccion_taco):
    def callback_refresco(tipo_refresco):
        anotacion_combinada = f"Refresco: {tipo_refresco}, Torta({seleccion_carne}), Tacos({seleccion_taco})"
        agregar_producto(nombre_paquete, anotacion_combinada)
    mostrar_ventana_refrescos("refresco", callback=callback_refresco)

def seleccionar_agua_paquete(nombre_paquete, seleccion_carne, seleccion_taco):
    def callback_agua(sabor_agua):
        anotacion_combinada = f"Agua: {sabor_agua}, Torta({seleccion_carne}), Tacos({seleccion_taco})"
        agregar_producto_paquete_agua(nombre_paquete, anotacion_combinada)
    mostrar_ventana_sabores("agua fresca", callback=callback_agua)

def agregar_producto_paquete_bebida(nombre, anotacion_bebida, extra_precio=0, cantidad_predeterminada=1):
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos: grupos.append("General")
    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({ "nombre": "Envío", "anotacion": None, "precio": 15, "grupo": "General", "cantidad": 1 })
    cantidad = max(1, int(cantidad_predeterminada))
    precio_base = menu_productos[nombre] + extra_precio
    item = {
        "nombre": nombre,
        "anotacion": anotacion_bebida,
        "precio": precio_base * cantidad,
        "grupo": grupo_actual,
        "cantidad": cantidad
    }
    pedido_actual.append(item)
    actualizar_ticket()

def agregar_producto_paquete_agua(nombre, sabor_agua):
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos: grupos.append("General")
    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({ "nombre": "Envío", "anotacion": None, "precio": 15, "grupo": "General", "cantidad": 1 })
    
    precio_base = menu_productos[nombre]
    
    ventana_item = tk.Toplevel(ventana)
    ventana_item.title(f"Agregar {nombre}")
    ventana_item.geometry("400x320")
    ventana_item.configure(bg="#e6d2a1")
    tk.Label(ventana_item, text="Cantidad:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=(10, 2))
    frame_cantidad = tk.Frame(ventana_item, bg="#e6d2a1")
    frame_cantidad.pack(pady=5)
    font_widgets = ("Roboto", 16, "bold")
    cantidad_entry = tk.Entry(frame_cantidad, font=font_widgets, width=5, justify='center')
    cantidad_entry.insert(0, "1")
    def decrementar_cantidad():
        try:
            valor_actual = int(cantidad_entry.get())
            if valor_actual > 1:
                cantidad_entry.delete(0, tk.END)
                cantidad_entry.insert(0, str(valor_actual - 1))
        except ValueError:
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, "1")
    def incrementar_cantidad():
        try:
            valor_actual = int(cantidad_entry.get())
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, str(valor_actual + 1))
        except ValueError:
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, "1")
    btn_menos = tk.Button(frame_cantidad, text="-", font=font_widgets, command=decrementar_cantidad, bg="#d32f2f", fg="white", relief="flat")
    btn_mas = tk.Button(frame_cantidad, text="+", font=font_widgets, command=incrementar_cantidad, bg="#4CAF50", fg="white", relief="flat")
    btn_menos.pack(side=tk.LEFT, padx=10)
    cantidad_entry.pack(side=tk.LEFT, padx=5)
    btn_mas.pack(side=tk.LEFT, padx=10)
    tk.Label(ventana_item, text="Nota:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=8)
    nota_entry = tk.Entry(ventana_item, font=("Roboto", 12), width=30)
    nota_entry.pack(pady=8)
    def confirmar():
        try:
            cantidad = int(cantidad_entry.get())
            if cantidad <= 0: raise ValueError("Cantidad debe ser mayor a 0.")
            nota_adicional = nota_entry.get()
            if sabor_agua and nota_adicional: anotacion_final = f"{sabor_agua}, {nota_adicional}"
            elif sabor_agua: anotacion_final = sabor_agua
            elif nota_adicional: anotacion_final = nota_adicional
            else: anotacion_final = sabor_agua
            precio_final = precio_base * cantidad
            item = { "nombre": nombre, "anotacion": anotacion_final, "precio": precio_final, "grupo": grupo_actual, "cantidad": cantidad }
            pedido_actual.append(item)
            ventana_item.destroy()
            actualizar_ticket()
        except ValueError as e: messagebox.showerror("Error", f"Entrada inválida: {e}", parent=ventana_item)
    tk.Button(ventana_item, text="Confirmar", font=("Roboto", 12), bg="#4caf50", fg="white", command=confirmar, width=15, pady=5).pack(pady=15)
    ventana_item.transient(ventana)

def _agregar_carne_gramos_callback(carne_seleccionada):
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos: grupos.append("General")
    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({ "nombre": "Envío", "anotacion": None, "precio": 15, "grupo": "General", "cantidad": 1 })
    ventana_carne = tk.Toplevel(ventana)
    ventana_carne.title("Carne(Gramos)")
    ventana_carne.geometry("420x470")
    ventana_carne.configure(bg="#e6d2a1")
    tk.Label(ventana_carne, text="Gramos:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=5)
    gramos_entry = tk.Entry(ventana_carne, font=("Roboto", 12), width=20)
    gramos_entry.pack(pady=2)
    frame_gramos_presets = tk.Frame(ventana_carne, bg="#e6d2a1")
    frame_gramos_presets.pack(pady=(3, 8))

    def seleccionar_gramos_preset(valor):
        gramos_entry.delete(0, tk.END)
        gramos_entry.insert(0, str(valor))
        dinero_entry.delete(0, tk.END)

    for texto, valor in [("50gr", 50), ("100gr", 100), ("250gr", 250), ("500gr", 500), ("1kg", 1000)]:
        btn_preset = tk.Button(
            frame_gramos_presets, text=texto, font=("Roboto", 10, "bold"),
            bg="#8d6e63", fg="white", relief="flat", padx=7, pady=3,
            command=lambda v=valor: seleccionar_gramos_preset(v)
        )
        btn_preset.pack(side="left", padx=3)

    tk.Label(ventana_carne, text="O Monto ($):", font=("Roboto", 12), bg="#e6d2a1").pack(pady=5)
    dinero_entry = tk.Entry(ventana_carne, font=("Roboto", 12), width=20)
    dinero_entry.pack(pady=2)
    frame_dinero_presets = tk.Frame(ventana_carne, bg="#e6d2a1")
    frame_dinero_presets.pack(pady=(3, 8))

    def seleccionar_dinero_preset(valor):
        dinero_entry.delete(0, tk.END)
        dinero_entry.insert(0, str(valor))
        gramos_entry.delete(0, tk.END)

    for texto, valor in [("$20", 20), ("$50", 50), ("$100", 100), ("$250", 250)]:
        btn_preset = tk.Button(
            frame_dinero_presets, text=texto, font=("Roboto", 10, "bold"),
            bg="#2e7d32", fg="white", relief="flat", padx=10, pady=3,
            command=lambda v=valor: seleccionar_dinero_preset(v)
        )
        btn_preset.pack(side="left", padx=4)

    tk.Label(ventana_carne, text="Nota:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=5)
    nota_entry = tk.Entry(ventana_carne, font=("Roboto", 12), width=30)
    nota_entry.pack(pady=2)
    def confirmar():
        try:
            gramos_str = gramos_entry.get().strip()
            dinero_str = dinero_entry.get().strip()
            precio_por_gramo = 0.3
            if not gramos_str and not dinero_str:
                messagebox.showerror("Error", "Debe ingresar gramos o monto.", parent=ventana_carne)
                return
            if gramos_str and dinero_str:
                messagebox.showerror("Error", "Ingrese solo un campo: gramos o monto.", parent=ventana_carne)
                return
            if gramos_str:
                gramos = float(gramos_str)
                if gramos <= 0: raise ValueError("Gramos debe ser positivo.")
                precio_final = gramos * precio_por_gramo
                gramos_final = gramos
            else:
                dinero = float(dinero_str)
                if dinero <= 0: raise ValueError("Monto debe ser positivo.")
                gramos_final = dinero / precio_por_gramo
                precio_final = dinero
            nota_adicional = nota_entry.get().strip()
            ventana_carne.destroy()
            if nota_adicional: anotacion = f"{carne_seleccionada}, {gramos_final:.2f}g, {nota_adicional}"
            else: anotacion = f"{carne_seleccionada}, {gramos_final:.2f}g"
            item = { "nombre": "Carne(Gramos)", "anotacion": anotacion, "precio": round(precio_final, 2), "grupo": grupo_actual, "cantidad": 1 }
            pedido_actual.append(item)
            actualizar_ticket()
        except ValueError as e: messagebox.showerror("Error", f"Entrada inválida: {e}", parent=ventana_carne)
    tk.Button(ventana_carne, text="Confirmar", font=("Roboto", 12), bg="#4caf50", fg="white", command=confirmar, width=15, pady=5).pack(pady=15)
    ventana_carne.transient(ventana)

def agregar_carne_gramos():
    mostrar_ventana_seleccion_carne(_agregar_carne_gramos_callback)

def agregar_nuevo_item():
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos: grupos.append("General")
    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({ "nombre": "Envío", "anotacion": None, "precio": 15, "grupo": "General", "cantidad": 1 })
    nombre = simpledialog.askstring("Nuevo Ítem", "Ingresa el nombre del nuevo ítem:", parent=ventana)
    if not nombre: return
    precio = simpledialog.askfloat("Precio", f"Ingresa el precio para {nombre}:", minvalue=0, parent=ventana)
    if precio is None: return
    anotacion = simpledialog.askstring("Anotación", f"Alguna nota para {nombre}?", parent=ventana)
    if nombre and precio is not None:
        item = { "nombre": nombre, "anotacion": anotacion, "precio": precio, "grupo": grupo_actual, "cantidad": 1 }
        pedido_actual.append(item)
        actualizar_ticket()

def agregar_descuento():
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos: grupos.append("General")
    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({ "nombre": "Envío", "anotacion": None, "precio": 15, "grupo": "General", "cantidad": 1 })
    monto = simpledialog.askfloat("Descuento", "Ingresa el monto del descuento:", minvalue=0, parent=ventana)
    if monto is None: return
    anotacion = simpledialog.askstring("Nota del Descuento", "Ingresa una nota para el descuento (opcional):", parent=ventana)
    item = { "nombre": f"Descuento", "anotacion": anotacion, "precio": -monto, "grupo": grupo_actual, "cantidad": 1 }
    pedido_actual.append(item)
    actualizar_ticket()

def modificar_precio_item(nombre):
    nuevo_precio = simpledialog.askfloat("Modificar Precio", f"Ingrese el nuevo precio para {nombre}:", minvalue=0, parent=ventana)
    if nuevo_precio is not None:
        menu_productos[nombre] = nuevo_precio
        guardar_precios()
        messagebox.showinfo("Éxito", f"El precio de {nombre} ha sido actualizado a ${nuevo_precio:.2f}.", parent=ventana)
        mostrar_ventana_modificar_precio()
    else:
        messagebox.showwarning("Cancelado", "No se modificó el precio.", parent=ventana)

def mostrar_ventana_modificar_precio():
    clave_archivo = "clave.txt"
    if not os.path.exists(clave_archivo):
        with open(clave_archivo, "w") as f: f.write("123")
    with open(clave_archivo, "r") as f: clave_guardada = f.read().strip()
    clave = simpledialog.askstring("Contraseña", "Ingrese la contraseña para modificar precios:", show="*", parent=ventana)
    if clave != clave_guardada:
        messagebox.showerror("Acceso denegado", "Contraseña incorrecta.", parent=ventana)
        return
    ventana_precios = tk.Toplevel(ventana)
    ventana_precios.title("Modificar Precios del Menú")
    window_width = max(int(screen_width * 0.4), 400)
    window_height = max(int(screen_height * 0.5), 400)
    ventana_precios.geometry(f"{window_width}x{window_height}")
    ventana_precios.configure(bg="#e6d2a1")
    ventana_precios.resizable(True, True)
    ventana_precios.minsize(400, 400)
    tk.Label(ventana_precios, text="Modificar Precios del Menú", font=("Roboto", 14, "bold"), bg="#e6d2a1", fg="#d32f2f").pack(pady=10, fill="x")
    canvas = tk.Canvas(ventana_precios, bg="#ffffff")
    scrollbar = tk.Scrollbar(ventana_precios, orient="vertical", command=canvas.yview)
    frame_menu = tk.Frame(canvas, bg="#ffffff")
    frame_menu.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_menu, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")
    categorias = {
        "Comida": ["Torta", "Taco Dorado", "Taco Blandito", "Taco con Carne", "Torta Mini"],
        "Bebidas": ["Refresco", "Agua Chica", "Agua Grande", "Caguama", "Cerveza"],
        "Paquetes": ["Paquete 1", "Paquete 2", "Paquete 3", "Paquete 4", "Paquete 5"]
    }
    for categoria, items in categorias.items():
        tk.Label(frame_menu, text=categoria, font=("Roboto", 11, "bold"), bg="#ffffff", fg="#3e2723").pack(anchor="w", pady=5, padx=10)
        for nombre in items:
            if nombre in menu_productos:
                frame_item = tk.Frame(frame_menu, bg="#ffffff")
                frame_item.pack(fill="x", pady=2, padx=20)
                tk.Label(frame_item, text=f"{nombre}: ${menu_productos[nombre]:.2f}", font=("Roboto", 10), bg="#ffffff", fg="#3e2723", anchor="w").pack(side="left")
                btn_modificar = tk.Button(frame_item, text="Modificar", font=("Roboto", 10), bg="#ff6f00", fg="white", relief="flat",
                                          activebackground="#ef6c00", command=lambda n=nombre: modificar_precio_item(n))
                btn_modificar.pack(side="right", padx=5)
                btn_modificar.bind("<Enter>", lambda e, b=btn_modificar: b.config(bg="#ef6c00"))
                btn_modificar.bind("<Leave>", lambda e, b=btn_modificar: b.config(bg="#ff6f00"))
    ventana_precios.protocol("WM_DELETE_WINDOW", lambda: ventana_precios.destroy())

def agregar_producto(nombre, sabor=None):
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos: grupos.append("General")
    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({ "nombre": "Envío", "anotacion": None, "precio": 15, "grupo": "General", "cantidad": 1 })
    precio_base = menu_productos[nombre]
    ventana_item = tk.Toplevel(ventana)
    ventana_item.title(f"Agregar {nombre}")
    ventana_item.geometry("400x320")
    ventana_item.configure(bg="#e6d2a1")
    tk.Label(ventana_item, text="Cantidad:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=(10, 2))
    frame_cantidad = tk.Frame(ventana_item, bg="#e6d2a1")
    frame_cantidad.pack(pady=5)
    font_widgets = ("Roboto", 16, "bold")
    cantidad_entry = tk.Entry(frame_cantidad, font=font_widgets, width=5, justify='center')
    cantidad_entry.insert(0, "1")
    def decrementar_cantidad():
        try:
            valor_actual = int(cantidad_entry.get())
            if valor_actual > 1:
                cantidad_entry.delete(0, tk.END)
                cantidad_entry.insert(0, str(valor_actual - 1))
        except ValueError:
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, "1")
    def incrementar_cantidad():
        try:
            valor_actual = int(cantidad_entry.get())
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, str(valor_actual + 1))
        except ValueError:
            cantidad_entry.delete(0, tk.END)
            cantidad_entry.insert(0, "1")
    btn_menos = tk.Button(frame_cantidad, text="-", font=font_widgets, command=decrementar_cantidad, bg="#d32f2f", fg="white", relief="flat")
    btn_mas = tk.Button(frame_cantidad, text="+", font=font_widgets, command=incrementar_cantidad, bg="#4CAF50", fg="white", relief="flat")
    btn_menos.pack(side=tk.LEFT, padx=10)
    cantidad_entry.pack(side=tk.LEFT, padx=5)
    btn_mas.pack(side=tk.LEFT, padx=10)
    tk.Label(ventana_item, text="Nota:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=8)
    nota_entry = tk.Entry(ventana_item, font=("Roboto", 12), width=30)
    nota_entry.pack(pady=8)
    def confirmar():
        try:
            cantidad = int(cantidad_entry.get())
            if cantidad <= 0: raise ValueError("Cantidad debe ser mayor a 0.")
            nota_adicional = nota_entry.get()
            if sabor and nota_adicional: anotacion_final = f"{sabor}, {nota_adicional}"
            elif sabor: anotacion_final = sabor
            elif nota_adicional: anotacion_final = nota_adicional
            else: anotacion_final = None
            precio_final = precio_base * cantidad
            item = { "nombre": nombre, "anotacion": anotacion_final, "precio": precio_final, "grupo": grupo_actual, "cantidad": cantidad }
            pedido_actual.append(item)
            ventana_item.destroy()
            actualizar_ticket()
        except ValueError as e: messagebox.showerror("Error", f"Entrada inválida: {e}", parent=ventana_item)
    tk.Button(ventana_item, text="Confirmar", font=("Roboto", 12), bg="#4caf50", fg="white", command=confirmar, width=15, pady=5).pack(pady=15)
    ventana_item.transient(ventana)

def renombrar_grupo(nombre_viejo):
    ventana_rename = tk.Toplevel(ventana)
    ventana_rename.title("Editar Nombre")
    ventana_rename.geometry("380x220")
    ventana_rename.configure(bg="#faf2d3")
    ventana_rename.resizable(False, False)
    ventana_rename.transient(ventana)
    ventana_rename.grab_set()
    
    # Header
    header_rename = tk.Frame(ventana_rename, bg="#d32f2f", height=45)
    header_rename.pack(fill="x")
    header_rename.pack_propagate(False)
    tk.Label(header_rename, text="✏️  Editar Nombre", font=("Roboto", 13, "bold"),
             bg="#d32f2f", fg="white").pack(expand=True)
    
    # Contenido
    frame_contenido = tk.Frame(ventana_rename, bg="#faf2d3")
    frame_contenido.pack(fill="both", expand=True, padx=25, pady=15)
    
    tk.Label(frame_contenido, text=f"Nombre actual:  {nombre_viejo}", font=("Roboto", 10),
             bg="#faf2d3", fg="#6d4c41").pack(anchor="w", pady=(0, 8))
    
    tk.Label(frame_contenido, text="Nuevo nombre:", font=("Roboto", 11, "bold"),
             bg="#faf2d3", fg="#3e2723").pack(anchor="w", pady=(0, 4))
    
    entry_nuevo = tk.Entry(frame_contenido, font=("Roboto", 12), relief="solid", bd=1,
                           bg="#ffffff", highlightthickness=2, highlightcolor="#d32f2f",
                           highlightbackground="#d7c6a0")
    entry_nuevo.pack(fill="x", ipady=4)
    entry_nuevo.insert(0, nombre_viejo)
    entry_nuevo.select_range(0, tk.END)
    entry_nuevo.focus_set()
    
    # Botones
    frame_btns = tk.Frame(frame_contenido, bg="#faf2d3")
    frame_btns.pack(fill="x", pady=(15, 0))
    
    def confirmar_rename():
        nuevo_nombre = entry_nuevo.get().strip()
        if nuevo_nombre and nuevo_nombre != nombre_viejo:
            if nombre_viejo in grupos:
                idx = grupos.index(nombre_viejo)
                grupos[idx] = nuevo_nombre
            for item in pedido_actual:
                if item.get("grupo") == nombre_viejo:
                    item["grupo"] = nuevo_nombre
            global grupo_actual
            if grupo_actual == nombre_viejo:
                grupo_actual = nuevo_nombre
            ventana_rename.destroy()
            actualizar_ticket()
        elif not nuevo_nombre:
            entry_nuevo.config(highlightcolor="#ff0000", highlightbackground="#ff0000")
        else:
            ventana_rename.destroy()
    
    btn_cancelar = tk.Button(frame_btns, text="Cancelar", font=("Roboto", 10, "bold"),
                             bg="#e0e0e0", fg="#3e2723", relief="flat", padx=16, pady=4,
                             command=ventana_rename.destroy, cursor="hand2")
    btn_cancelar.pack(side="left", padx=(0, 8))
    btn_cancelar.bind("<Enter>", lambda e: btn_cancelar.config(bg="#bdbdbd"))
    btn_cancelar.bind("<Leave>", lambda e: btn_cancelar.config(bg="#e0e0e0"))
    
    btn_guardar = tk.Button(frame_btns, text="Guardar", font=("Roboto", 10, "bold"),
                            bg="#4caf50", fg="white", relief="flat", padx=16, pady=4,
                            command=confirmar_rename, cursor="hand2")
    btn_guardar.pack(side="right")
    btn_guardar.bind("<Enter>", lambda e: btn_guardar.config(bg="#388e3c"))
    btn_guardar.bind("<Leave>", lambda e: btn_guardar.config(bg="#4caf50"))
    
    entry_nuevo.bind("<Return>", lambda e: confirmar_rename())
    entry_nuevo.bind("<Escape>", lambda e: ventana_rename.destroy())

def crear_grupo():
    global grupo_actual
    nombre = generar_nombre_plato_unico()
    grupo_actual = nombre
    if nombre not in grupos: grupos.append(nombre)
    actualizar_ticket()

def generar_nombre_plato_unico():
    global plato_counter
    while True:
        plato_counter += 1
        nombre = f"Plato {plato_counter}"
        if nombre not in grupos:
            return nombre

def duplicar_grupo(grupo_origen):
    global grupo_actual
    nuevo_nombre = generar_nombre_plato_unico()
    # Copiar todos los items del grupo origen al nuevo grupo, excepto Envío (solo debe existir uno)
    items_a_copiar = [
        item for item in pedido_actual
        if item.get("grupo") == grupo_origen and item.get("nombre") != "Envío"
    ]
    for item in items_a_copiar:
        nuevo_item = copy.deepcopy(item)
        nuevo_item["grupo"] = nuevo_nombre
        pedido_actual.append(nuevo_item)
    grupo_actual = nuevo_nombre
    if nuevo_nombre not in grupos: grupos.append(nuevo_nombre)
    actualizar_ticket()

def actualizar_ticket():
    for widget in frame_resumen.winfo_children(): widget.destroy()
    canvas = tk.Canvas(frame_resumen, bg="#ffffff")
    scrollbar = tk.Scrollbar(frame_resumen, orient="vertical", command=canvas.yview)
    frame_contenedor = tk.Frame(canvas, bg="#ffffff")
    frame_contenedor.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_contenedor, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    total = 0
    columna_actual = tk.Frame(frame_contenedor, bg="#ffffff")
    columna_actual.pack(fill="x", padx=15, anchor="n")
    if not pedido_actual:
        tk.Label(columna_actual, text="(Sin productos aún)", font=("Roboto", 11, "italic"), fg="#6d4c41", bg="#ffffff").pack(pady=15)
    else:
        items_agrupados = {}
        for item in pedido_actual:
            grupo = item.get("grupo", "General")
            items_agrupados.setdefault(grupo, []).append(item)
        for grupo in sorted(items_agrupados.keys(), key=lambda x: (x == "General", x)):
            frame_plato = tk.Frame(columna_actual, bg="#fffdf7", bd=2, relief="groove", highlightthickness=1, highlightbackground="#e0c684")
            frame_plato.pack(fill="x", pady=(8, 4), padx=2)

            es_activo = (grupo == grupo_actual)
            bg_header = "#ffd54f" if es_activo else "#f5f0e0"
            fg_header = "#3e2723"
            fila_grupo = tk.Frame(frame_plato, bg="#fffdf7")
            fila_grupo.pack(fill="x", pady=(8, 2), padx=8)

            # Rectangulo del nombre del plato (seleccionable)
            frame_grupo_header = tk.Frame(fila_grupo, bg=bg_header, cursor="hand2", bd=1, relief="solid")
            frame_grupo_header.pack(side="left", fill="x", expand=True)
            
            # Indicador de selección
            indicador = "▸ " if es_activo else "  "
            lbl_grupo = tk.Label(frame_grupo_header, text=f"{indicador}{grupo}", font=("Roboto", 11, "bold"),
                anchor="w", bg=bg_header, fg=fg_header, padx=6, pady=4)
            lbl_grupo.pack(side="left")
            
            frame_acciones_grupo = tk.Frame(fila_grupo, bg="#fffdf7")
            frame_acciones_grupo.pack(side="right", padx=(6, 0))

            btn_editar_grupo = tk.Button(frame_acciones_grupo, text="Editar nombre", font=("Roboto", 8, "bold"),
                bg="#ffa726", fg="white", relief="flat", bd=0, cursor="hand2",
                activebackground="#fb8c00",
                command=lambda g=grupo: renombrar_grupo(g))
            btn_editar_grupo.pack(side="right", padx=(4, 0), ipadx=4, ipady=2)
            btn_editar_grupo.bind("<Enter>", lambda e, b=btn_editar_grupo: b.config(bg="#fb8c00"))
            btn_editar_grupo.bind("<Leave>", lambda e, b=btn_editar_grupo: b.config(bg="#ffa726"))
            
            btn_duplicar_grupo = tk.Button(frame_acciones_grupo, text="Duplicar plato", font=("Roboto", 8, "bold"),
                bg="#43a047", fg="white", relief="flat", bd=0, cursor="hand2",
                activebackground="#2e7d32",
                command=lambda g=grupo: duplicar_grupo(g))
            btn_duplicar_grupo.pack(side="right", ipadx=4, ipady=2)
            btn_duplicar_grupo.bind("<Enter>", lambda e, b=btn_duplicar_grupo: b.config(bg="#2e7d32"))
            btn_duplicar_grupo.bind("<Leave>", lambda e, b=btn_duplicar_grupo: b.config(bg="#43a047"))
            
            # Hacer clickeable todo el header para seleccionar grupo
            def seleccionar_grupo(g=grupo):
                global grupo_actual
                grupo_actual = g
                if g not in grupos:
                    grupos.append(g)
                actualizar_ticket()
            
            for widget in [frame_grupo_header, lbl_grupo]:
                widget.bind("<Button-1>", lambda e, g=grupo: seleccionar_grupo(g))
            tk.Label(frame_plato, text="Producto          | Cantidad | Precio", font=("Roboto", 11, "bold"), anchor="w", bg="#fffdf7", fg="#3e2723").pack(anchor="w", padx=8)
            tk.Label(frame_plato, text="-" * 40, font=("Roboto", 11), anchor="w", bg="#fffdf7", fg="#3e2723").pack(anchor="w", padx=8)
            for item in items_agrupados[grupo]:
                producto = item["nombre"][:18].ljust(18)
                cantidad = str(item["cantidad"]).center(8)
                precio = f"${item['precio']:.2f}".rjust(10)
                texto = f"{producto} | {cantidad} | {precio}"
                if item["anotacion"]: texto += f"\n{dividir_texto(item['anotacion'])}"
                fila = tk.Frame(frame_plato, bg="#fffdf7")
                fila.pack(fill="x", pady=3, padx=8)
                tk.Label(fila, text=texto, anchor="w", justify="left", bg="#fffdf7", font=("Roboto", 11), fg="#3e2723").pack(side="left", fill="x", expand=True)
                idx = pedido_actual.index(item)
                btn_eliminar = tk.Button(fila, text="X", fg="white", bg="#d32f2f", command=lambda idx=idx: eliminar_item(idx), width=3, relief="flat", font=("Roboto", 10))
                btn_eliminar.pack(side="right")
                btn_eliminar.bind("<Enter>", lambda e: btn_eliminar.config(bg="#b71c1c"))
                btn_eliminar.bind("<Leave>", lambda e: btn_eliminar.config(bg="#d32f2f"))
                total += item['precio']
    frame_total = tk.Frame(frame_resumen, bg="#ffffff")
    frame_total.pack(pady=15, anchor="w")
    tk.Label(frame_total, text="TOTAL:", font=("Roboto", 12, "bold"), bg="#ffffff", fg="#000000", pady=10, padx=5, relief="flat").pack(side="left")
    tk.Label(frame_total, text=f"${total:.2f}", font=("Roboto", 12, "bold"), bg="#ffffff", fg="#d32f2f", pady=10, padx=5, relief="flat").pack(side="left")

def eliminar_item(indice):
    del pedido_actual[indice]
    actualizar_ticket()

# --- NUEVA FUNCIÓN: CONTADOR DE PEDIDOS ---
def obtener_siguiente_numero_pedido():
    hoy = date.today().isoformat()
    archivo = f"historial_{hoy}.txt"
    if not os.path.exists(archivo):
        return "01"
    
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            contenido = f.read()
            conteo = contenido.count("===== PEDIDO")
            return f"{conteo + 1:02d}"
    except Exception:
        return "01"

def guardar_en_historial(fecha_hora, domicilio, total, numero_pedido):
    hoy = date.today().isoformat()
    telefono = ""
    if var_telefono.get() == 1: telefono = entry_telefono.get().strip()
    cruces = entry_cruces.get().strip()
    items_copy = copy.deepcopy(pedido_actual)
    with open(f"historial_{hoy}.txt", "a", encoding="utf-8") as f:
        f.write(f"===== PEDIDO - {fecha_hora} =====\n")
        f.write(f"N. Pedido: {numero_pedido}\n") # Se guarda en el txt
        f.write(f"Fecha y Hora: {fecha_hora}\n")
        f.write(f"Domicilio: {domicilio.strip()}\n")
        if telefono: f.write(f"Teléfono: {telefono}\n")
        f.write(f"Cruces: {cruces}\n")
        if hora_especifica: f.write(f"Hora Específica: {hora_especifica.strip()}\n")
        f.write("--- Productos ---\n")
        items_agrupados = {}
        for item in items_copy:
            grupo = item.get("grupo", "General")
            items_agrupados.setdefault(grupo, []).append(item)
        for grupo in sorted(items_agrupados.keys(), key=lambda x: (x == "General", x)):
            f.write(f"\nCliente: {grupo.upper()}\n")
            for item in items_agrupados[grupo]:
                f.write(f"  - {item['nombre']} (x{item['cantidad']}) (${item['precio']:.2f})\n")
                if item['anotacion']: f.write(dividir_texto(item['anotacion'], 32, "    Nota: ") + "\n")
        f.write(f"\nTotal: ${total:.2f}\n")
        f.write("=" * 35  + "\n\n")
    print(f"[SAVE] Guardado en historial: {len(pedido_actual)} productos, Total: ${total:.2f}, N. Pedido: {numero_pedido}")
    
    # --- AUTO-ACTUALIZAR LISTA DE PEDIDOS SI ESTÁ ABIERTA ---
    refresh_lista_pedidos_si_abierta()

def verificar_impresora():
    try:
        printer_name = win32print.GetDefaultPrinter()
        if not printer_name: return False, "No se encontró una impresora predeterminada. Configura una en el sistema."
        printers = win32print.EnumPrinters(2)
        printer_encontrada = False
        for printer in printers:
            if printer[2] == printer_name:
                printer_encontrada = True
                break
        if not printer_encontrada: return False, f"La impresora '{printer_name}' no está disponible."
        return True, printer_name
    except Exception as e: return False, f"Error al verificar la impresora: {str(e)}"

def imprimir_texto(texto, doc_name="Documento"):
    try:
        impresora_ok, resultado = verificar_impresora()
        if not impresora_ok:
            messagebox.showerror("Error de Impresora", resultado)
            return False
        printer_name = resultado
        print(f"[PRINT] Intentando imprimir en: {printer_name}")
        hprinter = win32print.OpenPrinter(printer_name)
        hdc = win32ui.CreateDC()
        try: hdc.CreatePrinterDC(printer_name)
        except win32ui.error as e:
            messagebox.showerror("Error", f"No se pudo crear el contexto de dispositivo: {str(e)}")
            win32print.ClosePrinter(hprinter)
            return False
        hdc.StartDoc(doc_name)
        hdc.StartPage()
        try:
            font = win32ui.CreateFont({ "name": "Arial", "height": 30, "weight": FW_NORMAL })
            hdc.SelectObject(font)
        except win32ui.error as e:
            messagebox.showerror("Error", f"No se pudo configurar la fuente: {str(e)}")
            hdc.EndPage()
            hdc.EndDoc()
            win32print.ClosePrinter(hprinter)
            return False
        y = 20
        lineas_procesadas = 0
        for line in texto.split('\n'):
            try:
                hdc.TextOut(20, y, line.rstrip())
                y += 30
                lineas_procesadas += 1
            except Exception as e:
                print(f"Error imprimiendo linea {lineas_procesadas}: {e}")
                continue
        hdc.EndPage()
        hdc.EndDoc()
        win32print.ClosePrinter(hprinter)
        print(f"[SUCCESS] Impresion completada: {lineas_procesadas} lineas procesadas")
        messagebox.showinfo("Éxito", f"{doc_name} impreso correctamente.")
        return True
    except win32print.error as e:
        error_msg = f"Error de impresora: {str(e)}. Verifica que esté conectada y configurada."
        messagebox.showerror("Error de Impresión", error_msg)
        print(f"[ERROR] Error win32print: {e}")
        return False
    except Exception as e:
        error_msg = f"Error inesperado al imprimir: {str(e)}"
        messagebox.showerror("Error de Impresión", error_msg)
        print(f"[ERROR] Error general: {e}")
        return False

# MODIFICADO: Agregado parametro numero_pedido y lógica para Agua Grande
def imprimir_ticket_personalizado(fecha, domicilio, telefono, cruces, total, items, numero_pedido="01"):
    global hora_especifica
    try:
        ticket = f"{centrar('TORTAS AHOGADAS')}\n"
        ticket += f"{centrar('DOÑA SUSY')}\n"
        # --- N. PEDIDO MOVIDO AL FINAL ---
        ticket += f"{centrar('Geranio #869A')}\n"
        ticket += f"{centrar('Col.Tulipanes CP:45647')}\n"
        ticket += f"{centrar('33-3684-4525')}\n"
        ticket += "=" * 32 + "\n"
        ticket += dividir_campo(domicilio, "Domicilio: ") + "\n"
        if telefono: ticket += dividir_campo(telefono, "Telefono: ") + "\n"
        ticket += dividir_campo(cruces, "Cruces: ") + "\n"
        ticket += f"Fecha: {fecha}\n"
        if hora_especifica: ticket += f"Hora especifica: {hora_especifica}\n"
        ticket += "=" * 32 + "\n"
        ticket += "Prod          | Cant | Precio\n"
        ticket += "-" * 32 + "\n"
        items_agrupados = {}
        for item in items:
            grupo = item.get("grupo", "General")
            items_agrupados.setdefault(grupo, []).append(item)
        for grupo in sorted(items_agrupados.keys(), key=lambda x: (x == "General", x)):
            ticket += f"Cliente: {grupo.upper()}\n"
            for item in items_agrupados[grupo]:
                producto = item["nombre"][:14].ljust(14)
                cantidad = str(item["cantidad"]).center(6)
                precio = f"${item['precio']:.2f}".rjust(10)
                ticket += f"{producto}|{cantidad}|{precio}\n"
                if item['anotacion']: ticket += dividir_texto(item['anotacion']) + "\n"
            ticket += "=================================\n"
        ticket += "=" * 32 + "\n"
        ticket += f"{centrar(f'TOTAL: ${total:.2f}')}\n"
        ticket += "=" * 32 + "\n" # Separador extra
        
        # --- CALCULANDO RESUMEN BEBIDAS ---
        refrescos = {}
        aguas_frescas = {}
        for item in items:
            nombre = item["nombre"]
            cantidad = item["cantidad"]
            anotacion = item.get("anotacion", "") or ""
            if nombre == "Refresco":
                tipo_refresco = anotacion.split(",")[0].strip() if anotacion else "Sin especificar"
                refrescos[tipo_refresco] = refrescos.get(tipo_refresco, 0) + cantidad
            elif nombre in ["Paquete 1", "Paquete 2"]:
                if "agua fresca" in anotacion.lower() or "Agua:" in anotacion:
                    # SIEMPRE GRANDE
                    if "jamaica" in anotacion.lower(): 
                        aguas_frescas["Jamaica Grande"] = aguas_frescas.get("Jamaica Grande", 0) + cantidad
                    elif "horchata" in anotacion.lower(): 
                        aguas_frescas["Horchata Grande"] = aguas_frescas.get("Horchata Grande", 0) + cantidad
                    else: 
                        aguas_frescas["Agua Fresca Grande"] = aguas_frescas.get("Agua Fresca Grande", 0) + cantidad
                else:
                    for tipo in ["COCA", "FANTA", "MANZA", "SPRITE", "COCA LIGHT"]: # Agregado COCA LIGHT
                        if tipo in anotacion:
                            refrescos[tipo] = refrescos.get(tipo, 0) + cantidad
                            break
                    else:
                        if anotacion and "agua fresca" not in anotacion.lower():
                            tipo_refresco = anotacion.split(",")[0].strip().replace("Refresco: ", "")
                            refrescos[tipo_refresco] = refrescos.get(tipo_refresco, 0) + cantidad
            elif nombre in ["Agua Chica", "Agua Grande"]:
                tamaño = "Chica" if nombre == "Agua Chica" else "Grande"
                if "jamaica" in anotacion.lower():
                    clave = f"Jamaica {tamaño}"
                    aguas_frescas[clave] = aguas_frescas.get(clave, 0) + cantidad
                elif "horchata" in anotacion.lower():
                    clave = f"Horchata {tamaño}"
                    aguas_frescas[clave] = aguas_frescas.get(clave, 0) + cantidad
                else:
                    sabor = anotacion.split(",")[0].strip() if anotacion else "Sin especificar"
                    clave = f"{sabor} {tamaño}"
                    aguas_frescas[clave] = aguas_frescas.get(clave, 0) + cantidad
        
        # --- IMPRIMIR RESUMEN (SI EXISTE) ---
        if refrescos or aguas_frescas:
            if refrescos:
                ticket += f"{centrar('RESUMEN DE REFRESCOS:')}\n"
                for tipo, cant in refrescos.items(): ticket += f"{centrar(f'{tipo}: {cant}')}\n"
            if aguas_frescas:
                ticket += f"{centrar('RESUMEN DE AGUAS FRESCAS:')}\n"
                for sabor, cant in aguas_frescas.items(): ticket += f"{centrar(f'{sabor}: {cant}')}\n"
            ticket += "=" * 32 + "\n"

        # --- N. PEDIDO AL FINAL ---
        ticket += f"{centrar(f'N. PEDIDO: {numero_pedido}')}\n" 
        ticket += "=" * 32 + "\n"
        ticket += f"{centrar('Gracias por su pedido')}\n"
        ticket += "=" * 32 + "\n"
        
        return ticket
    except Exception as e:
        print(f"[ERROR] Error generando ticket: {e}")
        return f"Error generando ticket: {str(e)}"

def obtener_ultimo_ticket_guardado():
    hoy = date.today().isoformat()
    archivo = f"historial_{hoy}.txt"
    if not os.path.exists(archivo): return None
    try:
        with open(archivo, "r", encoding="utf-8") as f: contenido = f.read().strip()
        if not contenido: return None
        pedidos = contenido.split("===== PEDIDO - ")[1:]
        if not pedidos: return None
        ultimo_pedido = pedidos[-1]
        lineas = ultimo_pedido.strip().split("\n")
        ultimo_ticket = { "domicilio": "", "telefono": "", "cruces": "", "hora_especifica": None, "items": [], "total": 0 }
        grupo_actual = None
        for i, linea in enumerate(lineas[1:], 1):
            linea = linea.strip()
            if linea.startswith("Domicilio:"): ultimo_ticket["domicilio"] = linea.replace("Domicilio:", "").strip()
            elif linea.startswith("Teléfono:"): ultimo_ticket["telefono"] = linea.replace("Teléfono:", "").strip()
            elif linea.startswith("Cruces:"): ultimo_ticket["cruces"] = linea.replace("Cruces:", "").strip()
            elif linea.startswith("Hora Específica:"):
                hora_str = linea.replace("Hora Específica:", "").strip()
                ultimo_ticket["hora_especifica"] = hora_str if hora_str else None
            elif linea.startswith("Cliente:"): grupo_actual = linea.replace("Cliente:", "").strip()
            elif linea.startswith("  - "):
                producto_linea = linea.replace("  - ", "").strip()
                try:
                    if "(x" in producto_linea and ") ($" in producto_linea:
                        nombre = producto_linea.split(" (x")[0].strip()
                        resto = producto_linea.split(" (x")[1]
                        cantidad = int(resto.split(") ($")[0])
                        precio = float(resto.split(") ($")[1].replace(")", ""))
                    else:
                        nombre = producto_linea.split(" ($")[0].strip()
                        precio = float(producto_linea.split(" ($")[1].replace(")", ""))
                        cantidad = 1
                    item = { "nombre": nombre, "cantidad": cantidad, "precio": precio, "grupo": grupo_actual or "General", "anotacion": None }
                    ultimo_ticket["items"].append(item)
                except (ValueError, IndexError) as e:
                    print(f"[ERROR] Error procesando linea de producto: {producto_linea} - {e}")
                    continue
            elif linea.startswith("    Nota:") and ultimo_ticket["items"]:
                nota = linea.replace("    Nota:", "").strip()
                if ultimo_ticket["items"][-1]["anotacion"]: ultimo_ticket["items"][-1]["anotacion"] += " " + nota
                else: ultimo_ticket["items"][-1]["anotacion"] = nota
            elif linea.startswith("Total:"):
                total_str = linea.replace("Total:", "").replace("$", "").strip()
                ultimo_ticket["total"] = float(total_str)
        return ultimo_ticket
    except Exception as e:
        print(f"[ERROR] Error al leer ultimo ticket: {e}")
        return None

def tickets_son_iguales(ticket_actual, ultimo_ticket):
    if ultimo_ticket is None: return False
    if ticket_actual["domicilio"].strip() != ultimo_ticket["domicilio"].strip(): return False
    if ticket_actual["telefono"].strip() != ultimo_ticket["telefono"].strip(): return False
    if ticket_actual["cruces"].strip() != ultimo_ticket["cruces"].strip(): return False
    if abs(ticket_actual["total"] - ultimo_ticket["total"]) > 0.01: return False
    if len(ticket_actual["items"]) != len(ultimo_ticket["items"]): return False
    productos_actual = []
    productos_ultimo = []
    for item in ticket_actual["items"]:
        producto_str = f"{item['nombre']}|{item['cantidad']}|{item['precio']:.2f}|{item.get('grupo', 'General')}|{item.get('anotacion', '') or ''}"
        productos_actual.append(producto_str)
    for item in ultimo_ticket["items"]:
        producto_str = f"{item['nombre']}|{item['cantidad']}|{item['precio']:.2f}|{item.get('grupo', 'General')}|{item.get('anotacion', '') or ''}"
        productos_ultimo.append(producto_str)
    productos_actual.sort()
    productos_ultimo.sort()
    if productos_actual != productos_ultimo: return False
    return True

def imprimir_ticket():
    try:
        domicilio = entry_domicilio.get().strip()
        telefono = ""
        if var_telefono.get() == 1: telefono = entry_telefono.get().strip()
        cruces = entry_cruces.get().strip()
        if not domicilio or (var_telefono.get() == 1 and not telefono) or not cruces:
            messagebox.showwarning("Faltan datos", "Debes llenar domicilio, cruces y teléfono (si está activado).")
            return
        if not pedido_actual:
            messagebox.showwarning("Sin productos", "Agrega al menos un producto antes de imprimir.")
            return
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")
        total = sum(item['precio'] for item in pedido_actual)
        items_copy = copy.deepcopy(pedido_actual)
        ticket_actual = { "domicilio": domicilio, "telefono": telefono, "cruces": cruces, "hora_especifica": hora_especifica.strip() if hora_especifica else None, "items": items_copy, "total": total }
        ultimo_ticket = obtener_ultimo_ticket_guardado()
        es_duplicado = tickets_son_iguales(ticket_actual, ultimo_ticket) if ultimo_ticket else False
        
        if var_telefono.get() == 1 and telefono: guardar_actualizar_cliente(telefono, domicilio, cruces)
        
        # Obtenemos número de pedido para el ticket
        num_pedido = obtener_siguiente_numero_pedido()

        if es_duplicado:
            respuesta = messagebox.askyesno("Ticket Duplicado Detectado", "Este ticket es identico al anterior.\n\n¿Deseas imprimir de todas formas?\n\n(No se guardara en el historial)", icon="warning")
            if not respuesta: return
            # Si es duplicado, no guardamos en historial, pero pasamos el numero (el numero será el siguiente disponible aunque no se guarde)
        else: 
            guardar_en_historial(fecha_hora, domicilio, total, num_pedido)
        
        # Pasar num_pedido a la función de generación
        ticket_contenido = imprimir_ticket_personalizado(fecha_hora, domicilio, telefono, cruces, total, items_copy, num_pedido)
        
        if "Error generando ticket" in ticket_contenido:
            messagebox.showerror("Error", "No se pudo generar el contenido del ticket.")
            return
        imprimir_texto(ticket_contenido, f"Ticket {num_pedido}")
    except Exception as e:
        error_msg = f"Error inesperado en imprimir_ticket: {str(e)}"
        messagebox.showerror("Error", error_msg)

def imprimir_ticket_directo(ticket_texto):
    imprimir_texto(ticket_texto, "Ticket")

def mostrar_resumen_dia():
    clave_archivo = "clave.txt"
    if not os.path.exists(clave_archivo):
        with open(clave_archivo, "w") as f: f.write("123")
    with open(clave_archivo, "r") as f: clave_guardada = f.read().strip()
    clave = simpledialog.askstring("Contraseña", "Contraseña:", show="*", parent=ventana)
    if clave != clave_guardada:
        messagebox.showerror("Acceso denegado", "Incorrecta.")
        return
    hoy = date.today().isoformat()
    archivo = f"historial_{hoy}.txt"
    if not os.path.exists(archivo):
        messagebox.showinfo("Sin historial", "Sin pedidos.")
        return
    def eliminar_pedido(indice):
        with open(archivo, "r", encoding="utf-8") as f: contenido = f.read().strip().split("===== PEDIDO - ")[1:]
        if 0 <= indice < len(contenido):
            contenido.pop(indice)
            with open(archivo, "w", encoding="utf-8") as f:
                for i, pedido in enumerate(contenido, 1):
                    primera_linea_pedido = pedido.split('\n')[0]
                    f.write(f"==== PEDIDO - {primera_linea_pedido} ====\n")
                    f.write("\n".join(pedido.split("\n")[1:]) + "\n\n")
            ventana_resumen.destroy()
            mostrar_resumen_dia()
    ventana_resumen = tk.Toplevel(ventana)
    ventana_resumen.title("Resumen del Día")
    window_width = max(int(screen_width * 0.8), 900)
    window_height = max(int(screen_height * 0.8), 700)
    ventana_resumen.geometry(f"{window_width}x{window_height}")
    ventana_resumen.configure(bg="#f5f5f5")
    ventana_resumen.minsize(900, 700)
    header_frame = tk.Frame(ventana_resumen, bg="#4caf50", height=70)
    header_frame.pack(fill="x", pady=(0, 15))
    header_frame.pack_propagate(False)
    tk.Label(header_frame, text="📊 Resumen del Día", font=("Roboto", 18, "bold"), bg="#4caf50", fg="white").pack(expand=True)
    main_container = tk.Frame(ventana_resumen, bg="#f5f5f5")
    main_container.pack(fill="both", expand=True, padx=20)
    left_frame = tk.Frame(main_container, bg="white", relief="solid", bd=1)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
    pedidos_header = tk.Frame(left_frame, bg="#e3f2fd", height=40)
    pedidos_header.pack(fill="x")
    pedidos_header.pack_propagate(False)
    tk.Label(pedidos_header, text="🛍️ PEDIDOS DEL DÍA", font=("Roboto", 12, "bold"), bg="#e3f2fd", fg="#1976d2").pack(expand=True)
    canvas = tk.Canvas(left_frame, bg="white")
    scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
    frame_lista_pedidos = tk.Frame(canvas, bg="white")
    frame_lista_pedidos.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_lista_pedidos, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    right_frame = tk.Frame(main_container, bg="white", relief="solid", bd=1, width=400)
    right_frame.pack(side="right", fill="y", padx=(10, 0))
    right_frame.pack_propagate(False)
    stats_header = tk.Frame(right_frame, bg="#fff3e0", height=40)
    stats_header.pack(fill="x")
    stats_header.pack_propagate(False)
    tk.Label(stats_header, text="📈 ESTADÍSTICAS", font=("Roboto", 12, "bold"), bg="#fff3e0", fg="#e65100").pack(expand=True)
    total_general = 0
    pedidos = []
    refrescos_detalle = {}
    aguas_detalle = {}
    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.read().strip().split("===== PEDIDO - ")
        for pedido in contenido[1:]:
            lineas = pedido.strip().split("\n")
            if len(lineas) < 2: continue
            fecha_hora = lineas[0].strip()
            fecha = fecha_hora.split()[0]
            domicilio = ""
            total = 0
            items_pedido = []
            for linea in lineas:
                if linea.startswith("Domicilio:"): domicilio = linea.replace("Domicilio:", "").strip()
                elif linea.startswith("Total:"):
                    total_str = linea.replace("Total:", "").replace("$", "").strip()
                    try:
                        total = float(total_str)
                        total_general += total
                        pedidos.append((domicilio, fecha, total))
                    except ValueError: continue
                elif linea.startswith("  - "):
                    nombre_item = linea.split("(x")[0].replace("  - ", "").strip()
                    try:
                        cantidad = int(linea.split("(x")[1].split(")")[0]) if "(x" in linea else 1
                        items_pedido.append({"nombre": nombre_item, "cantidad": cantidad})
                    except (IndexError, ValueError): continue
                elif linea.startswith("    Nota:"):
                    if items_pedido:
                        anotacion = linea.replace("    Nota:", "").strip()
                        items_pedido[-1]["anotacion"] = anotacion
            for item in items_pedido:
                nombre = item["nombre"]
                cantidad = item["cantidad"]
                anotacion = item.get("anotacion", "") or ""
                if nombre == "Refresco":
                    tipo_refresco = anotacion.split(",")[0].strip() if anotacion else "Sin especificar"
                    refrescos_detalle[tipo_refresco] = refrescos_detalle.get(tipo_refresco, 0) + cantidad
                elif nombre in ["Paquete 1", "Paquete 2"]:
                    # --- MODIFICADO: Mapeo de agua de paquete a "Grande" en Resumen también ---
                    if "agua fresca" in anotacion.lower():
                        if "agua fresca jamaica" in anotacion.lower() or "jamaica" in anotacion.lower():
                            aguas_detalle["Jamaica Grande"] = aguas_detalle.get("Jamaica Grande", 0) + cantidad
                        elif "agua fresca horchata" in anotacion.lower() or "horchata" in anotacion.lower():
                            aguas_detalle["Horchata Grande"] = aguas_detalle.get("Horchata Grande", 0) + cantidad
                        else:
                            aguas_detalle["Agua Fresca Grande"] = aguas_detalle.get("Agua Fresca Grande", 0) + cantidad
                    else:
                        for tipo in ["COCA", "FANTA", "MANZA", "SPRITE", "COCA LIGHT"]: # Agregado COCA LIGHT
                            if tipo in anotacion:
                                refrescos_detalle[tipo] = refrescos_detalle.get(tipo, 0) + cantidad
                                break
                        else:
                            if anotacion and "agua fresca" not in anotacion.lower():
                                tipo_refresco = anotacion.split(",")[0].strip()
                                refrescos_detalle[tipo_refresco] = refrescos_detalle.get(tipo_refresco, 0) + cantidad
                elif nombre in ["Agua Chica", "Agua Grande"]:
                    tamaño = "Chica" if nombre == "Agua Chica" else "Grande"
                    if "jamaica" in anotacion.lower():
                        clave = f"Jamaica {tamaño}"
                        aguas_detalle[clave] = aguas_detalle.get(clave, 0) + cantidad
                    elif "horchata" in anotacion.lower():
                        clave = f"Horchata {tamaño}"
                        aguas_detalle[clave] = aguas_detalle.get(clave, 0) + cantidad
                    else:
                        sabor = anotacion.split(",")[0].strip() if anotacion else "Sin especificar"
                        clave = f"{sabor} {tamaño}"
                        aguas_detalle[clave] = aguas_detalle.get(clave, 0) + cantidad
    if not pedidos:
        tk.Label(frame_lista_pedidos, text="No hay datos para mostrar", font=("Roboto", 12), bg="white", fg="#666").pack(pady=30)
    else:
        for i, (domicilio, fecha, total) in enumerate(pedidos):
            pedido_frame = tk.Frame(frame_lista_pedidos, bg="#f8f9fa", relief="solid", bd=1)
            pedido_frame.pack(fill="x", padx=15, pady=5)
            info_frame = tk.Frame(pedido_frame, bg="#f8f9fa")
            info_frame.pack(fill="x", padx=10, pady=8)
            tk.Label(info_frame, text=f"🏠 {domicilio[:25]}{'...' if len(domicilio) > 25 else ''}", font=("Roboto", 10, "bold"), bg="#f8f9fa", fg="#333").pack(side="left")
            middle_frame = tk.Frame(info_frame, bg="#f8f9fa")
            middle_frame.pack(side="left", expand=True)
            tk.Label(middle_frame, text=f"📅 {fecha}", font=("Roboto", 9), bg="#f8f9fa", fg="#666").pack()
            tk.Label(info_frame, text=f"💰 ${int(total)}", font=("Roboto", 10, "bold"), bg="#f8f9fa", fg="#d32f2f").pack(side="right")
            btn_eliminar = tk.Button(info_frame, text="❌", fg="white", bg="#d32f2f", command=lambda idx=i: eliminar_pedido(idx), width=3, relief="flat", font=("Roboto", 8))
            btn_eliminar.pack(side="right", padx=(5, 0))
            btn_eliminar.bind("<Enter>", lambda e: btn_eliminar.config(bg="#b71c1c"))
            btn_eliminar.bind("<Leave>", lambda e: btn_eliminar.config(bg="#d32f2f"))
    stats_content = tk.Frame(right_frame, bg="white")
    stats_content.pack(fill="both", expand=True, padx=15, pady=15)
    total_frame = tk.Frame(stats_content, bg="#e8f5e8", relief="solid", bd=1)
    total_frame.pack(fill="x", pady=(0, 15))
    tk.Label(total_frame, text="💰 TOTAL GENERAL", font=("Roboto", 12, "bold"), bg="#e8f5e8", fg="#2e7d32").pack(pady=5)
    tk.Label(total_frame, text=f"${int(total_general)}", font=("Roboto", 16, "bold"), bg="#e8f5e8", fg="#1b5e20").pack(pady=(0, 10))
    if refrescos_detalle:
        refrescos_frame = tk.Frame(stats_content, bg="#fff3e0", relief="solid", bd=1)
        refrescos_frame.pack(fill="x", pady=(0, 10))
        tk.Label(refrescos_frame, text="🥤 REFRESCOS VENDIDOS", font=("Roboto", 11, "bold"), bg="#fff3e0", fg="#e65100").pack(pady=5)
        for tipo, cantidad in sorted(refrescos_detalle.items()):
            item_frame = tk.Frame(refrescos_frame, bg="#fff3e0")
            item_frame.pack(fill="x", padx=10, pady=1)
            tk.Label(item_frame, text=f"• {tipo}:", font=("Roboto", 9), bg="#fff3e0", fg="#333").pack(side="left")
            tk.Label(item_frame, text=f"{cantidad}", font=("Roboto", 9, "bold"), bg="#fff3e0", fg="#d84315").pack(side="right")
        tk.Label(refrescos_frame, text="", bg="#fff3e0").pack(pady=2)
    if aguas_detalle:
        aguas_frame = tk.Frame(stats_content, bg="#e3f2fd", relief="solid", bd=1)
        aguas_frame.pack(fill="x", pady=(0, 10))
        tk.Label(aguas_frame, text="🧊 AGUAS FRESCAS VENDIDAS", font=("Roboto", 11, "bold"), bg="#e3f2fd", fg="#1976d2").pack(pady=5)
        for tipo, cantidad in sorted(aguas_detalle.items()):
            item_frame = tk.Frame(aguas_frame, bg="#e3f2fd")
            item_frame.pack(fill="x", padx=10, pady=1)
            tk.Label(item_frame, text=f"• {tipo}:", font=("Roboto", 9), bg="#e3f2fd", fg="#333").pack(side="left")
            tk.Label(item_frame, text=f"{cantidad}", font=("Roboto", 9, "bold"), bg="#e3f2fd", fg="#0d47a1").pack(side="right")
        tk.Label(aguas_frame, text="", bg="#e3f2fd").pack(pady=2)
    def imprimir_resumen_moderno():
        try:
            printer_name = win32print.GetDefaultPrinter()
            if not printer_name:
                messagebox.showerror("Error", "No se encontró una impresora predeterminada.")
                return
            resumen = "=============================\n"
            resumen += "Resumen del Día\n"
            resumen += "=============================\n"
            for i, (domicilio, fecha, total) in enumerate(pedidos): resumen += f"| {domicilio[:20].ljust(20)} | ${int(total)}\n"
            resumen += "=============================\n"
            if refrescos_detalle:
                resumen += "REFRESCOS VENDIDOS:\n"
                for tipo, cantidad in sorted(refrescos_detalle.items()): resumen += f"  {tipo}: {cantidad}\n"
                resumen += "=============================\n"
            if aguas_detalle:
                resumen += "AGUAS FRESCAS VENDIDAS:\n"
                for tipo, cantidad in sorted(aguas_detalle.items()): resumen += f"  {tipo}: {cantidad}\n"
                resumen += "=============================\n"
            resumen += f"TOTAL GENERAL: ${int(total_general)}\n"
            resumen += "=============================\n"
            hprinter = win32print.OpenPrinter(printer_name)
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            hdc.StartDoc("Resumen del Día")
            hdc.StartPage()
            font = win32ui.CreateFont({ "name": "Arial", "height": 30, "weight": FW_NORMAL })
            hdc.SelectObject(font)
            y = 20
            for line in resumen.split('\n'):
                hdc.TextOut(10, y, line.rstrip())
                y += 30
            hdc.EndPage()
            hdc.EndDoc()
            win32print.ClosePrinter(hprinter)
            messagebox.showinfo("Éxito", "Resumen del Día impreso correctamente.")
        except Exception as e: messagebox.showerror("Error", f"No se pudo imprimir: {str(e)}")
    boton_imprimir = tk.Button(stats_content, text="🖨️ Imprimir Resumen", font=("Roboto", 11, "bold"), bg="#4caf50", fg="white", relief="flat", command=imprimir_resumen_moderno)
    boton_imprimir.pack(fill="x", pady=15)
    boton_imprimir.bind("<Enter>", lambda e: boton_imprimir.config(bg="#388e3c"))
    boton_imprimir.bind("<Leave>", lambda e: boton_imprimir.config(bg="#4caf50"))

def convertir_hora_a_minutos(hora_str):
    try:
        if not hora_str: return 9999
        hora_str = hora_str.strip().upper()
        hora_str = hora_str.replace(" AM", "AM").replace(" PM", "PM")
        hora_str = hora_str.replace("A.M.", "AM").replace("P.M.", "PM")
        es_pm = "PM" in hora_str
        es_am = "AM" in hora_str
        hora_limpia = hora_str.replace("AM", "").replace("PM", "").strip()
        if not es_am and not es_pm:
            hora_temp = int(hora_limpia.split(":")[0]) if ":" in hora_limpia else int(hora_limpia)
            if 7 <= hora_temp <= 11: es_am = True
            else: es_pm = True
        if ":" in hora_limpia:
            partes = hora_limpia.split(":")
            horas = int(partes[0])
            minutos = int(partes[1])
        else:
            horas = int(hora_limpia)
            minutos = 0
        if es_am:
            if horas == 12: horas = 0
        elif es_pm:
            if horas != 12: horas += 12
        total_minutos = horas * 60 + minutos
        return total_minutos
    except Exception as e: return 9999

def refresh_lista_pedidos_si_abierta():
    global ventana_lista_instance
    if ventana_lista_instance is not None and tk.Toplevel.winfo_exists(ventana_lista_instance):
        try:
            ventana_lista_instance.refresh_func()
        except:
            pass

def imprimir_ticket_desde_lista(texto, n_ped):
    res = imprimir_texto(texto, f"Ticket {n_ped}")
    if res:
        messagebox.showinfo("Impreso", "Ticket enviado correctamente.")
    if ventana_lista_instance and tk.Toplevel.winfo_exists(ventana_lista_instance):
        ventana_lista_instance.lift()
        ventana_lista_instance.focus_force()

# --- NUEVA VENTANA DE LISTA DE PEDIDOS OPTIMIZADA ---
def mostrar_lista_pedidos():
    global ventana_lista_instance
    
    # 1. SINGLETON: Si ya existe, traerla al frente y salir
    if ventana_lista_instance is not None and tk.Toplevel.winfo_exists(ventana_lista_instance):
        ventana_lista_instance.lift()
        ventana_lista_instance.focus_force()
        return

    hoy = date.today().isoformat()
    archivo = f"historial_{hoy}.txt"
    if not os.path.exists(archivo):
        messagebox.showinfo("Info", "No hay pedidos hoy.")
        return

    ventana_lista = tk.Toplevel(ventana)
    ventana_lista_instance = ventana_lista
    ventana_lista.title("Lista de Pedidos")

    w, h = min(int(screen_width * 0.95), 1250), min(int(screen_height * 0.9), 760)
    ventana_lista.geometry(f"{w}x{h}")
    ventana_lista.configure(bg="#f5f0de")

    header = tk.Frame(ventana_lista, bg="#d32f2f", height=56)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text="Lista de Pedidos del Día", font=("Roboto", 15, "bold"), bg="#d32f2f", fg="white").pack(side="left", padx=14)

    toolbar = tk.Frame(ventana_lista, bg="#faf2d3", bd=1, relief="solid")
    toolbar.pack(fill="x", padx=10, pady=(8, 6))
    lbl_resumen = tk.Label(toolbar, text="", font=("Roboto", 10, "bold"), bg="#faf2d3", fg="#3e2723")
    lbl_resumen.pack(side="left", padx=10, pady=8)

    frame_main = tk.Frame(ventana_lista, bg="#f5f0de")
    frame_main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def crear_columna(parent, titulo, color_titulo, color_fondo):
        contenedor = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        tk.Label(contenedor, text=titulo, font=("Roboto", 12, "bold"), bg=color_titulo, fg="white").pack(fill="x")
        canvas_wrap = tk.Frame(contenedor, bg="#ffffff")
        canvas_wrap.pack(fill="both", expand=True)
        canvas = tk.Canvas(canvas_wrap, bg=color_fondo, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_wrap, orient="vertical", command=canvas.yview)
        interior = tk.Frame(canvas, bg=color_fondo)
        window_id = canvas.create_window((0, 0), window=interior, anchor="nw")
        interior.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return contenedor, interior

    col_izq, frame_izq_contenido = crear_columna(frame_main, "Pedidos Sin Hora", "#6d4c41", "#ffffff")
    col_der, frame_der_contenido = crear_columna(frame_main, "Pedidos Con Hora", "#0288d1", "#fffaf0")
    col_izq.pack(side="left", fill="both", expand=True, padx=(0, 6))
    col_der.pack(side="left", fill="both", expand=True, padx=(6, 0))

    def parsear_pedido(lines):
        data = {
            "fecha_hora": "",
            "hora_esp": None,
            "n_pedido": "??",
            "domicilio": "Sin Domicilio",
            "telefono": "",
            "cruces": "No especificados",
            "total": 0.0,
            "items": []
        }
        grupo_en_curso = "General"
        item_en_curso = None

        if lines:
            primera = lines[0].replace("-", "", 1).replace("=", "").strip()
            if primera:
                data["fecha_hora"] = primera

        for l in lines:
            if l.startswith("N. Pedido:"):
                data["n_pedido"] = l.split(":", 1)[1].strip()
            elif l.startswith("Fecha y Hora:"):
                data["fecha_hora"] = l.split(":", 1)[1].strip()
            elif l.startswith("Domicilio:"):
                data["domicilio"] = l.split(":", 1)[1].strip()
            elif l.startswith("Teléfono:"):
                data["telefono"] = l.split(":", 1)[1].strip()
            elif l.startswith("Cruces:"):
                data["cruces"] = l.split(":", 1)[1].strip()
            elif l.startswith("Hora Específica:"):
                hora = l.split(":", 1)[1].strip()
                data["hora_esp"] = hora if hora else None
            elif l.startswith("Total:"):
                try:
                    data["total"] = float(l.replace("Total:", "").replace("$", "").strip())
                except ValueError:
                    data["total"] = 0.0
            elif l.startswith("Cliente:"):
                grupo_en_curso = l.split(":", 1)[1].strip() or "General"
            elif l.startswith("  - "):
                contenido = l.replace("  - ", "", 1).strip()
                nombre = contenido
                cantidad = 1
                precio = 0.0
                if " (x" in contenido and ") ($" in contenido:
                    nombre = contenido.split(" (x", 1)[0].strip()
                    try:
                        cantidad = int(contenido.split(" (x", 1)[1].split(")", 1)[0])
                    except ValueError:
                        cantidad = 1
                    try:
                        precio = float(contenido.rsplit("($", 1)[1].replace(")", "").strip())
                    except ValueError:
                        precio = 0.0
                item_en_curso = {
                    "nombre": nombre,
                    "anotacion": None,
                    "precio": precio,
                    "grupo": grupo_en_curso,
                    "cantidad": cantidad
                }
                data["items"].append(item_en_curso)
            elif l.startswith("    Nota:") and item_en_curso:
                nota = l.replace("    Nota:", "", 1).strip()
                item_en_curso["anotacion"] = nota
            elif l.startswith("          ") and item_en_curso and item_en_curso.get("anotacion"):
                item_en_curso["anotacion"] += " " + l.strip()

        return data

    def construir_ticket_impresion(p_data):
        global hora_especifica
        hora_anterior = hora_especifica
        try:
            hora_especifica = p_data["hora_esp"]
            return imprimir_ticket_personalizado(
                p_data["fecha_hora"],
                p_data["domicilio"],
                p_data["telefono"],
                p_data["cruces"],
                p_data["total"],
                p_data["items"],
                p_data["n_pedido"]
            )
        finally:
            hora_especifica = hora_anterior

    def texto_items_resumen(items):
        if not items:
            return "Sin productos"
        lineas = []
        for item in items:
            linea = f"- {item['nombre']} x{item['cantidad']} (${item['precio']:.2f})"
            if item.get("anotacion"):
                linea += f"\n  Nota: {item['anotacion']}"
            lineas.append(linea)
        return "\n".join(lineas)

    def borrar_pedido_historial(indice_objetivo):
        if not os.path.exists(archivo):
            return False
        with open(archivo, "r", encoding="utf-8") as f:
            bloques = f.read().split("===== PEDIDO")
        pedidos_bloques = bloques[1:]
        if indice_objetivo < 0 or indice_objetivo >= len(pedidos_bloques):
            return False
        pedidos_bloques.pop(indice_objetivo)
        with open(archivo, "w", encoding="utf-8") as f:
            for bloque in pedidos_bloques:
                contenido = bloque.strip()
                if contenido:
                    f.write(f"===== PEDIDO {contenido}\n\n")
        return True

    def cargar_pedido_en_principal(p_data):
        global pedido_actual, grupo_actual, grupos, hora_especifica

        if p_data["telefono"]:
            var_telefono.set(1)
            toggle_telefono_entry()
            entry_telefono.delete(0, tk.END)
            entry_telefono.insert(0, p_data["telefono"])
        else:
            var_telefono.set(0)
            toggle_telefono_entry()

        entry_cruces.delete(0, tk.END)
        entry_cruces.insert(0, p_data["cruces"])
        entry_domicilio.delete(0, tk.END)
        entry_domicilio.insert(0, p_data["domicilio"])

        if p_data["hora_esp"]:
            var_hora.set(1)
            toggle_hora_entry()
            entry_hora.delete(0, tk.END)
            entry_hora.insert(0, p_data["hora_esp"])
            hora_especifica = p_data["hora_esp"]
        else:
            var_hora.set(0)
            toggle_hora_entry()
            hora_especifica = None

        pedido_actual.clear()
        pedido_actual.extend(copy.deepcopy(p_data["items"]))

        grupos_detectados = []
        for item in pedido_actual:
            g = item.get("grupo", "General")
            if g not in grupos_detectados:
                grupos_detectados.append(g)
        if "General" not in grupos_detectados:
            grupos_detectados.insert(0, "General")
        grupos = grupos_detectados
        grupo_actual = grupos[0] if grupos else "General"

        actualizar_ticket()
        ventana.deiconify()
        ventana.lift()
        ventana.focus_force()

    def editar_pedido_desde_lista(p_data):
        confirmar = messagebox.askyesno(
            "Editar Pedido",
            "Este pedido se quitará del historial y se cargará en la pantalla principal para editarlo.\n\n¿Deseas continuar?",
            parent=ventana_lista
        )
        if not confirmar:
            return
        eliminado = borrar_pedido_historial(p_data["source_index"])
        if not eliminado:
            messagebox.showerror("Error", "No se pudo editar el pedido seleccionado.", parent=ventana_lista)
            return
        cargar_pedido_en_principal(p_data)
        messagebox.showinfo("Pedido cargado", "Pedido cargado para edición. Realiza cambios e imprime para guardarlo de nuevo.", parent=ventana)
        on_close()

    def pintar_card(parent, p_data):
        card = tk.Frame(parent, bg="#ffffff", relief="solid", bd=1)
        card.pack(fill="x", padx=8, pady=6)

        top = tk.Frame(card, bg="#faf2d3")
        top.pack(fill="x")
        tk.Label(top, text=f"Pedido #{p_data['n_pedido']}   Total: ${p_data['total']:.2f}", font=("Roboto", 11, "bold"), bg="#faf2d3", fg="#3e2723").pack(side="left", padx=8, pady=6)
        hora_texto = p_data["hora_esp"] if p_data["hora_esp"] else "Sin hora"
        tk.Label(top, text=hora_texto, font=("Roboto", 10, "bold"), bg="#faf2d3", fg="#0288d1").pack(side="right", padx=8)

        tk.Label(card, text=f"Domicilio: {p_data['domicilio']}", font=("Roboto", 11, "bold"), bg="#ffffff", fg="#3e2723", anchor="w", justify="left", wraplength=500).pack(fill="x", padx=8, pady=(6, 0))
        tk.Label(card, text=f"Tel: {p_data['telefono'] or 'S/N'}   |   Cruces: {p_data['cruces']}", font=("Roboto", 10), bg="#ffffff", fg="#5d4037", anchor="w", justify="left", wraplength=500).pack(fill="x", padx=8, pady=(2, 5))
        tk.Label(card, text=texto_items_resumen(p_data["items"]), font=("Consolas", 9), bg="#ffffff", fg="#3e2723", anchor="w", justify="left", wraplength=520).pack(fill="x", padx=8, pady=(0, 8))

        botonera = tk.Frame(card, bg="#ffffff")
        botonera.pack(fill="x", padx=8, pady=(0, 8))
        btn_imprimir = tk.Button(
            botonera,
            text="Imprimir Ticket",
            font=("Roboto", 10, "bold"),
            command=lambda: imprimir_ticket_desde_lista(p_data["print_text"], p_data["n_pedido"])
        )
        btn_imprimir.pack(side="left", fill="x", expand=True, padx=(0, 5))
        aplicar_estilo_boton(btn_imprimir, "#4caf50", "#388e3c")

        btn_editar = tk.Button(
            botonera,
            text="Editar",
            font=("Roboto", 10, "bold"),
            command=lambda: editar_pedido_desde_lista(p_data)
        )
        btn_editar.pack(side="left", fill="x", expand=True, padx=(5, 0))
        aplicar_estilo_boton(btn_editar, "#ff6f00", "#ef6c00")

    def cargar_datos():
        for widget in frame_izq_contenido.winfo_children():
            widget.destroy()
        for widget in frame_der_contenido.winfo_children():
            widget.destroy()

        if not os.path.exists(archivo):
            lbl_resumen.config(text="No hay pedidos registrados hoy")
            return

        with open(archivo, "r", encoding="utf-8") as f:
            bloques = f.read().strip().split("===== PEDIDO")

        pedidos = []
        for idx_bloque, bloque in enumerate(bloques[1:]):
            lines = [line for line in bloque.strip().split("\n") if line.strip()]
            if not lines:
                continue
            data = parsear_pedido(lines)
            data["print_text"] = construir_ticket_impresion(data)
            data["source_index"] = idx_bloque
            pedidos.append(data)

        sin_hora = [p for p in pedidos if not p["hora_esp"]]
        con_hora = [p for p in pedidos if p["hora_esp"]]

        sin_hora.reverse()
        con_hora.sort(key=lambda x: convertir_hora_a_minutos(x["hora_esp"]))

        lbl_resumen.config(
            text=f"Pedidos: {len(pedidos)}   |   Sin hora: {len(sin_hora)}   |   Con hora: {len(con_hora)}"
        )

        if not sin_hora:
            tk.Label(frame_izq_contenido, text="Sin pedidos normales", font=("Roboto", 11, "italic"), bg="#ffffff", fg="#6d4c41").pack(pady=12)
        if not con_hora:
            tk.Label(frame_der_contenido, text="Sin pedidos con hora", font=("Roboto", 11, "italic"), bg="#fffaf0", fg="#6d4c41").pack(pady=12)

        for p in sin_hora:
            pintar_card(frame_izq_contenido, p)
        for p in con_hora:
            pintar_card(frame_der_contenido, p)

    btn_refrescar = tk.Button(toolbar, text="Refrescar", font=("Roboto", 10, "bold"), command=lambda: cargar_datos())
    btn_refrescar.pack(side="right", padx=10, pady=6)
    aplicar_estilo_boton(btn_refrescar, "#0288d1", "#01579b")

    # Adjuntar función refresh a la instancia para llamarla desde fuera
    ventana_lista.refresh_func = cargar_datos
    
    # Manejar cierre para limpiar instancia global
    def on_close():
        global ventana_lista_instance
        ventana_lista_instance = None
        ventana_lista.destroy()
    
    ventana_lista.protocol("WM_DELETE_WINDOW", on_close)

    # Carga inicial
    cargar_datos()

def limpiar_pedido():
    global ventana_sabores, hora_especifica, grupo_actual, grupos, plato_counter
    pedido_actual.clear()
    for widget in frame_resumen.winfo_children(): widget.destroy()
    entry_domicilio.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    entry_cruces.delete(0, tk.END)
    hora_especifica = None
    var_hora.set(0)
    entry_hora.delete(0, tk.END)
    entry_hora.config(state="disabled")
    if ventana_sabores:
        ventana_sabores.destroy()
        ventana_sabores = None
    grupo_actual = "General"
    grupos = ["General"]
    plato_counter = 0
    actualizar_ticket()

def cambiar_contrasena():
    archivo_clave = "clave.txt"
    if not os.path.exists(archivo_clave):
        with open(archivo_clave, "w") as f: f.write("123")
    with open(archivo_clave, "r") as f: clave_actual = f.read().strip()
    entrada_actual = simpledialog.askstring("Cambiar contraseña", "Ingresa la contraseña actual:", show="*", parent=ventana)
    if entrada_actual != clave_actual:
        messagebox.showerror("Error", "Contraseña actual incorrecta.")
        return
    nueva_clave = simpledialog.askstring("Nueva contraseña", "Ingresa la nueva contraseña:", show="*", parent=ventana)
    if nueva_clave:
        with open(archivo_clave, "w") as f: f.write(nueva_clave)
        messagebox.showinfo("Éxito", "Contraseña actualizada correctamente.")

def toggle_hora_entry():
    global hora_especifica
    if var_hora.get() == 1:
        entry_hora.config(state="normal")
        entry_hora.focus()
    else:
        entry_hora.config(state="disabled")
        entry_hora.delete(0, tk.END)
        hora_especifica = None

def toggle_telefono_entry():
    if var_telefono.get() == 1:
        entry_telefono.config(state="normal")
        entry_telefono.bind("<KeyRelease>", lambda event: buscar_cliente(entry_telefono.get()))
    else:
        entry_telefono.delete(0, tk.END)
        entry_telefono.config(state="disabled")
        entry_telefono.unbind("<KeyRelease>")
        entry_domicilio.delete(0, tk.END)
        entry_cruces.delete(0, tk.END)

# --- NUEVA FUNCIÓN: MENÚ DE CONFIGURACIÓN ---
def mostrar_menu_configuracion():
    ventana_config = tk.Toplevel(ventana)
    ventana_config.title("Configuración")
    ventana_config.geometry("300x250")
    ventana_config.configure(bg="#e6d2a1")
    tk.Label(ventana_config, text="Opciones", font=("Roboto", 14, "bold"), bg="#e6d2a1", fg="#3e2723").pack(pady=10)
    btn_modificar = tk.Button(ventana_config, text="Modificar Precio", command=mostrar_ventana_modificar_precio, bg="#ff6f00", fg="white", font=("Roboto", 11), width=20)
    btn_modificar.pack(pady=5)
    btn_clave = tk.Button(ventana_config, text="Cambiar Contraseña", command=cambiar_contrasena, bg="#ff6f00", fg="white", font=("Roboto", 11), width=20)
    btn_clave.pack(pady=5)
    btn_resumen = tk.Button(ventana_config, text="Resumen del Día", command=mostrar_resumen_dia, bg="#0288d1", fg="white", font=("Roboto", 11), width=20)
    btn_resumen.pack(pady=5)

def aplicar_estilo_boton(btn, color_base, color_hover, fg="white"):
    btn.configure(
        bg=color_base,
        fg=fg,
        activebackground=color_hover,
        activeforeground=fg,
        relief="flat",
        bd=0,
        highlightthickness=0,
        cursor="hand2",
        padx=8,
        pady=6
    )
    btn.bind("<Enter>", lambda e, b=btn, c=color_hover: b.config(bg=c))
    btn.bind("<Leave>", lambda e, b=btn, c=color_base: b.config(bg=c))

def aplicar_estilo_entry(entry):
    entry.configure(
        relief="solid",
        bd=1,
        bg="#ffffff",
        highlightthickness=1,
        highlightbackground="#d7c6a0",
        highlightcolor="#ff6f00",
        insertbackground="#3e2723"
    )

# Inicializar la base de datos al inicio
inicializar_base_datos()

ventana = tk.Tk()
ventana.title("Tortas Ahogadas Doña Susy")
screen_width = ventana.winfo_screenwidth()
screen_height = ventana.winfo_screenheight()
window_width = min(int(screen_width * 0.95), 1152)
window_height = min(int(screen_height * 0.98), 1100)
ventana.geometry(f"{window_width}x{window_height}")
min_width = min(1000, max(640, int(screen_width * 0.88)))
min_height = min(700, max(560, int(screen_height * 0.65)))
ventana.minsize(min_width, min_height)
ventana.configure(bg="#e6d2a1")
ventana.resizable(True, True)

frame_principal = tk.Frame(ventana, bg="#e6d2a1")
frame_principal.pack(fill="both", expand=True, padx=10, pady=8)
frame_principal.grid_columnconfigure(0, weight=3)
frame_principal.grid_columnconfigure(1, weight=2)
frame_principal.grid_rowconfigure(0, weight=1)

panel_izquierdo = tk.Frame(frame_principal, bg="#ffffff", bd=1, relief="solid")
panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
frame_superior_izq = tk.Frame(panel_izquierdo, bg="#ffffff")
frame_superior_izq.pack(fill="both", padx=10, pady=6, expand=True)

tk.Label(frame_superior_izq, text="Tortas Ahogadas Doña Susy", font=("Roboto", 17, "bold"), bg="#ffffff", fg="#d32f2f", pady=2).pack(anchor="w", fill="x")
tk.Label(frame_superior_izq, text="Captura rápida de pedidos", font=("Roboto", 10), bg="#ffffff", fg="#6d4c41").pack(anchor="w", fill="x", pady=(0, 8))

frame_datos = tk.Frame(frame_superior_izq, bg="#faf2d3", bd=1, relief="solid")
frame_datos.pack(fill="x", padx=5, pady=5)

label_datos_cliente = tk.Label(frame_datos, text="Datos del Cliente", font=("Roboto", 12, "bold"), bg="#faf2d3", fg="#3e2723")
label_datos_cliente.pack(anchor="w", padx=10, pady=(8, 6))

frame_domicilio = tk.Frame(frame_datos, bg="#faf2d3")
frame_domicilio.pack(fill="x", padx=10, pady=3)
tk.Label(frame_domicilio, text="Domicilio:", width=18, anchor="w", bg="#faf2d3", font=("Roboto", 10), fg="#3e2723").pack(side="left")
entry_domicilio = tk.Entry(frame_domicilio, font=("Roboto", 10), relief="flat", bg="#ffffff", bd=1)
entry_domicilio.pack(side="left", padx=5, fill="x", expand=True)
aplicar_estilo_entry(entry_domicilio)

frame_telefono = tk.Frame(frame_datos, bg="#faf2d3")
frame_telefono.pack(fill="x", padx=10, pady=3)
tk.Label(frame_telefono, text="Teléfono:", width=18, anchor="w", bg="#faf2d3", font=("Roboto", 10), fg="#3e2723").pack(side="left")
var_telefono = tk.IntVar(value=1)
tk.Radiobutton(frame_telefono, text="Sí", variable=var_telefono, value=1, bg="#faf2d3", font=("Roboto", 10), fg="#3e2723", command=toggle_telefono_entry).pack(side="left", padx=5)
tk.Radiobutton(frame_telefono, text="No", variable=var_telefono, value=0, bg="#faf2d3", font=("Roboto", 10), fg="#3e2723", command=toggle_telefono_entry).pack(side="left", padx=5)
entry_telefono = tk.Entry(frame_telefono, font=("Roboto", 10), relief="flat", bg="#ffffff", bd=1)
entry_telefono.pack(side="left", padx=5, fill="x", expand=True)
aplicar_estilo_entry(entry_telefono)
entry_telefono.bind("<KeyRelease>", lambda event: buscar_cliente(entry_telefono.get()))

frame_cruces = tk.Frame(frame_datos, bg="#faf2d3")
frame_cruces.pack(fill="x", padx=10, pady=3)
tk.Label(frame_cruces, text="Cruces:", width=18, anchor="w", bg="#faf2d3", font=("Roboto", 10), fg="#3e2723").pack(side="left")
entry_cruces = tk.Entry(frame_cruces, font=("Roboto", 10), relief="flat", bg="#ffffff", bd=1)
entry_cruces.pack(side="left", padx=5, fill="x", expand=True)
aplicar_estilo_entry(entry_cruces)

frame_hora = tk.Frame(frame_datos, bg="#faf2d3")
frame_hora.pack(fill="x", padx=10, pady=3)
tk.Label(frame_hora, text="Hora en específico:", width=18, anchor="w", bg="#faf2d3", font=("Roboto", 10), fg="#3e2723").pack(side="left")
var_hora = tk.IntVar(value=0)
tk.Radiobutton(frame_hora, text="Sí", variable=var_hora, value=1, bg="#faf2d3", font=("Roboto", 10), fg="#3e2723", command=toggle_hora_entry).pack(side="left", padx=5)
tk.Radiobutton(frame_hora, text="No", variable=var_hora, value=0, bg="#faf2d3", font=("Roboto", 10), fg="#3e2723", command=toggle_hora_entry).pack(side="left", padx=5)
entry_hora = tk.Entry(frame_hora, font=("Roboto", 10), relief="flat", bg="#ffffff", bd=1, state="disabled")
entry_hora.pack(side="left", padx=5, fill="x", expand=True)
aplicar_estilo_entry(entry_hora)
def actualizar_hora(event):
    global hora_especifica
    if var_hora.get() == 1: hora_especifica = entry_hora.get()
    else: hora_especifica = None
entry_hora.bind("<KeyRelease>", actualizar_hora)

# --- TECLADO VIRTUAL DE WINDOWS 11 ---
_campos_cliente = None

def abrir_teclado_virtual(event=None):
    try:
        tabtip = r"C:\Program Files\Common Files\microsoft shared\ink\TabTip.exe"
        if os.path.exists(tabtip):
            subprocess.Popen([tabtip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

# Bind focus SOLO a los campos de datos del cliente
entry_domicilio.bind("<FocusIn>", abrir_teclado_virtual)
entry_telefono.bind("<FocusIn>", abrir_teclado_virtual)
entry_cruces.bind("<FocusIn>", abrir_teclado_virtual)
entry_hora.bind("<FocusIn>", abrir_teclado_virtual)

# --- MENÚ CON PESTAÑAS Y TARJETAS CUADRADAS ---
tk.Label(frame_superior_izq, text="Menú", bg="#ffffff", font=("Roboto", 16, "bold"), fg="#3e2723").pack(pady=(8, 6), anchor="w", padx=5)

# --- BARRA DE PESTAÑAS ---
frame_tabs = tk.Frame(frame_superior_izq, bg="#ffffff")
frame_tabs.pack(fill="x", padx=5, pady=(0, 8))

tab_actual = tk.StringVar(value="comida")

def crear_tabs():
    for widget in frame_tabs.winfo_children():
        widget.destroy()
    
    tabs_config = [
        ("comida", "🍽️  Comida", "#d32f2f", "#b71c1c"),
        ("paquetes", "📦  Paquetes", "#2e7d32", "#1b5e20"),
        ("bebidas", "🥤  Bebidas", "#0288d1", "#01579b"),
    ]
    
    for tab_id, texto, color_activo, color_hover in tabs_config:
        es_activo = tab_actual.get() == tab_id
        if es_activo:
            btn = tk.Button(frame_tabs, text=texto, font=("Roboto", 11, "bold"),
                           bg=color_activo, fg="white", relief="flat",
                           activebackground=color_hover, cursor="hand2",
                           bd=0, padx=20, pady=8,
                           command=lambda t=tab_id: cambiar_tab(t))
            btn.pack(side="left", padx=(0, 4))
            btn.bind("<Enter>", lambda e, b=btn, c=color_hover: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=color_activo: b.config(bg=c))
        else:
            btn = tk.Button(frame_tabs, text=texto, font=("Roboto", 11),
                           bg="#f5f0e0", fg="#3e2723", relief="flat",
                           activebackground="#e8e0c8", cursor="hand2",
                           bd=0, padx=20, pady=8,
                           command=lambda t=tab_id: cambiar_tab(t))
            btn.pack(side="left", padx=(0, 4))
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#e8e0c8"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#f5f0e0"))

# --- ÁREA DE CONTENIDO CON SCROLL ---
frame_grid_wrapper = tk.Frame(frame_superior_izq, bg="#ffffff")
frame_grid_wrapper.pack(fill="x", expand=False, pady=(2, 4))

canvas_grid = tk.Canvas(frame_grid_wrapper, bg="#ffffff", highlightthickness=0, height=265)
if screen_height <= 720:
    canvas_grid.configure(height=130)
elif screen_height <= 800:
    canvas_grid.configure(height=190)
frame_grid_interior = tk.Frame(canvas_grid, bg="#ffffff")
frame_grid_interior.bind("<Configure>", lambda e: canvas_grid.configure(scrollregion=canvas_grid.bbox("all")))
grid_window_id = canvas_grid.create_window((0, 0), window=frame_grid_interior, anchor="nw")
canvas_grid.bind("<Configure>", lambda e: canvas_grid.itemconfig(grid_window_id, width=e.width))
canvas_grid.pack(fill="x", expand=False)

# --- FUNCIÓN PARA CREAR TARJETA CUADRADA COMPACTA ---
def crear_tarjeta(parent, row, col, nombre, precio_texto, descripcion, emoji, color_bg, color_hover, command):
    card = tk.Frame(parent, bg=color_bg, bd=0, cursor="hand2", relief="flat")
    card.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
    
    # Contenido interno compacto
    inner = tk.Frame(card, bg=color_bg)
    inner.pack(fill="both", expand=True, padx=6, pady=5)
    
    # Fila superior: emoji + nombre
    lbl_nombre = tk.Label(inner, text=f"{emoji} {nombre.replace(chr(10), ' ')}", font=("Roboto", 9, "bold"),
                          bg=color_bg, fg="white", anchor="w", justify="left")
    lbl_nombre.pack(anchor="w", fill="x")
    
    # Precio
    lbl_precio = tk.Label(inner, text=precio_texto, font=("Roboto", 11, "bold"),
                          bg=color_bg, fg="#ffd54f", anchor="w")
    lbl_precio.pack(anchor="w", pady=(1, 0))
    
    # Descripción compacta
    lbl_desc = tk.Label(inner, text=descripcion, font=("Roboto", 7),
                        bg=color_bg, fg="#e0e0e0", anchor="w", justify="left", wraplength=145)
    lbl_desc.pack(anchor="w", fill="x")
    
    # Hover effect para toda la tarjeta
    all_widgets = [card, inner, lbl_nombre, lbl_precio, lbl_desc]
    
    def on_enter(e):
        for w in all_widgets:
            try: w.config(bg=color_hover)
            except: pass
    
    def on_leave(e):
        for w in all_widgets:
            try: w.config(bg=color_bg)
            except: pass
    
    for w in all_widgets:
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)
        w.bind("<Button-1>", lambda e: command())

# --- DATOS DE PRODUCTOS POR CATEGORÍA ---
productos_comida = [
    {"nombre": "Torta Ahogada", "precio": f"${menu_productos.get('Torta', 55)}", "desc": "Carne, Buche, Lengua,\nMixta", "emoji": "🥩",
     "color": "#8B2500", "hover": "#701E00",
     "command": lambda: mostrar_ventana_item_unificado("Torta", "carne")},
    {"nombre": "Torta Mini", "precio": f"${menu_productos.get('Torta Mini', 28)}", "desc": "Carne, Buche, Lengua,\nMixta", "emoji": "🥪",
     "color": "#A0522D", "hover": "#8B4513",
     "command": lambda: mostrar_ventana_item_unificado("Torta Mini", "carne")},
    {"nombre": "Taco Sencillo", "precio": f"${menu_productos.get('Taco Dorado', 10)}", "desc": "Papa, Frijol, Requesón\ny Picadillo", "emoji": "🌮",
     "color": "#BF6B00", "hover": "#A05A00",
     "command": lambda: mostrar_ventana_item_unificado("Taco Dorado", "taco")},
    {"nombre": "Taco Dorado c/Carne", "precio": f"${menu_productos.get('Taco con Carne', 25)}", "desc": "Carne, Buche, Lengua,\nMixta", "emoji": "🌮",
     "color": "#8B0000", "hover": "#700000",
     "command": lambda: mostrar_ventana_item_unificado("Taco Dorado c/Carne", "carne_taco")},
    {"nombre": "Taco Blandito", "precio": f"${menu_productos.get('Taco Blandito', 25)}", "desc": "Carne, Buche, Lengua,\nMixta", "emoji": "🌮",
      "color": "#A52A2A", "hover": "#8B1C1C",
     "command": lambda: mostrar_ventana_item_unificado("Taco Blandito", "carne")},
    {"nombre": "Carne\npor Gramos", "precio": "$$$", "desc": "Carne, Buche, Lengua,\nMixta", "emoji": "🥩",
     "color": "#6D4C41", "hover": "#5D4037",
     "command": agregar_carne_gramos},
    {"nombre": "Nuevo Ítem", "precio": "Custom", "desc": "Agrega un producto\npersonalizado", "emoji": "➕",
     "color": "#ff8f00", "hover": "#ef6c00",
     "command": agregar_nuevo_item},
    {"nombre": "Descuento", "precio": "- $", "desc": "Aplica un descuento\nal pedido", "emoji": "💲",
     "color": "#ff6f00", "hover": "#e65100",
     "command": agregar_descuento},
]

productos_paquetes = [
    {"nombre": "Paquete 1", "precio": f"${menu_productos.get('Paquete 1', 80)}", "desc": "Torta + Tacos\n+ Bebida", "emoji": "📦",
      "color": "#2e7d32", "hover": "#1b5e20",
     "command": lambda: (lambda cs={"cantidad": 1}: mostrar_ventana_seleccion_carne(
         lambda carne: mostrar_ventana_tipo_taco(
             lambda tipo: mostrar_ventana_bebida_paquete("Paquete 1", carne, tipo, cs), cs
         ),
         cs
     ))()},
    {"nombre": "Paquete 2", "precio": f"${menu_productos.get('Paquete 2', 85)}", "desc": "Torta + Tacos\n+ Bebida", "emoji": "📦",
      "color": "#388e3c", "hover": "#2e7d32",
     "command": lambda: (lambda cs={"cantidad": 1}: mostrar_ventana_seleccion_carne(
         lambda carne: mostrar_ventana_tipo_taco(
             lambda tipo: mostrar_ventana_bebida_paquete("Paquete 2", carne, tipo, cs), cs
         ),
         cs
     ))()},
    {"nombre": "Paquete 3", "precio": f"${menu_productos.get('Paquete 3', 205)}", "desc": "Paquete familiar\nmediano", "emoji": "📦",
     "color": "#43a047", "hover": "#388e3c",
     "command": lambda: agregar_producto("Paquete 3")},
    {"nombre": "Paquete 4", "precio": f"${menu_productos.get('Paquete 4', 320)}", "desc": "Paquete familiar\ngrande", "emoji": "📦",
     "color": "#4caf50", "hover": "#43a047",
     "command": lambda: agregar_producto("Paquete 4")},
    {"nombre": "Paquete 5", "precio": f"${menu_productos.get('Paquete 5', 630)}", "desc": "Paquete familiar\nextra grande", "emoji": "📦",
     "color": "#2e7d32", "hover": "#1b5e20",
     "command": lambda: agregar_producto("Paquete 5")},
]

productos_bebidas = [
    {"nombre": "Refresco", "precio": f"${menu_productos.get('Refresco', 25)}", "desc": "Coca, Fanta, Sprite,\nManzana, Coca Light", "emoji": "🥤",
      "color": "#0288d1", "hover": "#0277bd",
     "command": lambda: mostrar_ventana_item_unificado("Refresco", "refresco")},
    {"nombre": "Agua Chica", "precio": f"${menu_productos.get('Agua Chica', 15)}", "desc": "Jamaica, Horchata", "emoji": "💧",
      "color": "#0277bd", "hover": "#01579b",
     "command": lambda: mostrar_ventana_item_unificado("Agua Chica", "agua")},
    {"nombre": "Agua Grande", "precio": f"${menu_productos.get('Agua Grande', 25)}", "desc": "Jamaica, Horchata", "emoji": "💧",
      "color": "#01579b", "hover": "#014377",
     "command": lambda: mostrar_ventana_item_unificado("Agua Grande", "agua")},
    {"nombre": "Caguama", "precio": f"${menu_productos.get('Caguama', 70)}", "desc": "Cerveza tamaño\nfamiliar", "emoji": "🍺",
     "color": "#BF8C00", "hover": "#A07500",
     "command": lambda: agregar_producto("Caguama")},
    {"nombre": "Cerveza", "precio": f"${menu_productos.get('Cerveza', 25)}", "desc": "Cerveza individual", "emoji": "🍺",
     "color": "#D4A017", "hover": "#BF8C00",
     "command": lambda: agregar_producto("Cerveza")},
]

categorias_productos = {
    "comida": productos_comida,
    "paquetes": productos_paquetes,
    "bebidas": productos_bebidas,
}

def mostrar_productos_tab():
    # Limpiar grid
    for widget in frame_grid_interior.winfo_children():
        widget.destroy()
    
    productos = categorias_productos.get(tab_actual.get(), [])
    num_cols = 4
    
    for c in range(num_cols):
        frame_grid_interior.columnconfigure(c, weight=1, uniform="card")
    
    for i, prod in enumerate(productos):
        row = i // num_cols
        col = i % num_cols
        frame_grid_interior.rowconfigure(row, weight=1, uniform="cardrow")
        crear_tarjeta(
            frame_grid_interior, row, col,
            prod["nombre"], prod["precio"], prod["desc"], prod["emoji"],
            prod["color"], prod["hover"], prod["command"]
        )

def cambiar_tab(tab_id):
    tab_actual.set(tab_id)
    crear_tabs()
    mostrar_productos_tab()

# Inicializar tabs y productos
crear_tabs()
mostrar_productos_tab()

# --- SECCIÓN DE ACCIONES ---
frame_acciones = tk.Frame(frame_superior_izq, bg="#ffffff")
frame_acciones.pack(fill="x", pady=(4, 2))

frame_acciones.columnconfigure(0, weight=1)
frame_acciones.columnconfigure(1, weight=1)

btn_agregar_cliente = tk.Button(frame_acciones, text="Agregar Cliente", command=crear_grupo, 
                                bg="#4caf50", fg="white", font=("Roboto", 11, "bold"), relief="flat")
btn_agregar_cliente.grid(row=0, column=0, padx=5, pady=3, sticky="ew")
aplicar_estilo_boton(btn_agregar_cliente, "#4caf50", "#388e3c")

btn_imprimir_ticket = tk.Button(frame_acciones, text="Imprimir Ticket", command=imprimir_ticket, 
                                bg="#4caf50", fg="white", font=("Roboto", 11, "bold"), relief="flat")
btn_imprimir_ticket.grid(row=0, column=1, padx=5, pady=3, sticky="ew")
aplicar_estilo_boton(btn_imprimir_ticket, "#4caf50", "#388e3c")

btn_limpiar_pedido = tk.Button(frame_acciones, text="Limpiar Pedido", command=limpiar_pedido, 
                               bg="#d32f2f", fg="white", font=("Roboto", 11, "bold"), relief="flat")
btn_limpiar_pedido.grid(row=1, column=0, padx=5, pady=3, sticky="ew")
aplicar_estilo_boton(btn_limpiar_pedido, "#d32f2f", "#b71c1c")

btn_lista = tk.Button(frame_acciones, text="Lista de Pedidos", command=mostrar_lista_pedidos, 
                      bg="#0288d1", fg="white", font=("Roboto", 11, "bold"), relief="flat")
btn_lista.grid(row=1, column=1, padx=5, pady=3, sticky="ew")
aplicar_estilo_boton(btn_lista, "#0288d1", "#01579b")

# --- FOOTER ---
frame_footer_izq = tk.Frame(panel_izquierdo, bg="#ffd54f")
frame_footer_izq.pack(side="bottom", anchor="w", padx=5, pady=5)

img_engrane = cargar_icono("engrane.png", size=(30, 30))

btn_config = tk.Button(frame_footer_izq, image=img_engrane if img_engrane else None,
                        text="" if img_engrane else "Config", 
                        command=mostrar_menu_configuracion, 
                        bg="#ffd54f", relief="flat", activebackground="#ffca28")
if img_engrane: btn_config.image = img_engrane
btn_config.pack(padx=2, pady=2)

panel_derecho = tk.Frame(frame_principal, bg="#ffffff", bd=1, relief="solid")
panel_derecho.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
tk.Label(panel_derecho, text="Resumen del Pedido", font=("Roboto", 16, "bold"), bg="#ffffff", fg="#d32f2f").pack(anchor="w", pady=(10, 3), fill="x", padx=8)
tk.Label(panel_derecho, text="Verifica cantidades, notas y total antes de imprimir", font=("Roboto", 9), bg="#ffffff", fg="#6d4c41").pack(anchor="w", fill="x", padx=8, pady=(0, 6))
frame_resumen = tk.Frame(panel_derecho, bg="#ffffff")
frame_resumen.pack(fill="both", expand=True, anchor="n", padx=5)

# --- FUNCIÓN QUE FALTABA (AGREGADA) ---
def iniciar_ciclo_mensaje():
    global mensaje_activo
    if mensaje_activo:
        ventana.title("Tortas Ahogadas Doña Susy - ¡Ordena Aquí!")
    else:
        ventana.title("Tortas Ahogadas Doña Susy")
    mensaje_activo = not mensaje_activo
    ventana.after(1000, iniciar_ciclo_mensaje)
# --------------------------------------

watermark = tk.Label(ventana, text="Created By BrianP", font=("Roboto", 8), fg="#757575", bg="#e6d2a1")
watermark.place(relx=1.0, rely=1.0, anchor="se", x=-50, y=-20)

iniciar_ciclo_mensaje()
actualizar_ticket()
ventana.mainloop()
