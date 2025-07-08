import tkinter as tk
from tkinter import simpledialog, messagebox
import os
from datetime import datetime, date
import win32print
import win32ui
from win32con import *
import copy
import sqlite3
import json
import subprocess  # AGREGADO: Para abrir el teclado táctil

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

# FUNCIÓN PARA CONFIGURAR CODIFICACIÓN DE CONSOLA
def configurar_consola():
    """Configura la consola para manejar caracteres especiales"""
    try:
        import os
        # Configurar codificación UTF-8 en Windows
        if os.name == 'nt':
            os.system('chcp 65001 > nul')
        print("[INIT] Consola configurada correctamente")
    except Exception as e:
        print(f"[WARNING] No se pudo configurar la consola: {e}")

# FUNCIÓN CORREGIDA: Para abrir el teclado táctil de Windows
def abrir_teclado_tactil():
    """Abre el teclado táctil de Windows - FUNCIONA SIEMPRE"""
    try:
        # Abrir el teclado sin importar qué ventana esté activa
        subprocess.Popen("osk", shell=True)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el teclado táctil: {str(e)}")

# Cargar precios desde precios.json o usar valores por defecto
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
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar los precios: {str(e)}. Usando valores por defecto.")
        menu_productos = menu_productos_default.copy()

# Guardar precios en precios.json
def guardar_precios():
    try:
        with open("precios.json", "w", encoding="utf-8") as f:
            json.dump(menu_productos, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar los precios: {str(e)}.")

# Inicializar menu_productos
menu_productos = {}
cargar_precios()

# Configurar consola para evitar errores de codificación
configurar_consola()

pedido_actual = []
grupos = []
grupo_actual = None
ventana_sabores = None
hora_especifica = None

# Variables para el mensaje temporal
label_datos_cliente = None
mensaje_activo = False

def mostrar_mensaje_temporal():
    """Muestra el mensaje temporal por 5 segundos"""
    global label_datos_cliente, mensaje_activo
    if label_datos_cliente and not mensaje_activo:
        mensaje_activo = True
        label_datos_cliente.config(text="Datos del Cliente ( RECURDA Agregar Número de telefono REAL :)  )")
        # Programar que se oculte después de 5 segundos
        ventana.after(10000, ocultar_mensaje_temporal)

def ocultar_mensaje_temporal():
    """Oculta el mensaje temporal y programa que aparezca de nuevo en 30 segundos"""
    global label_datos_cliente, mensaje_activo
    if label_datos_cliente and mensaje_activo:
        mensaje_activo = False
        label_datos_cliente.config(text="Datos del Cliente")
        # Programar que aparezca de nuevo después de 30 segundos
        ventana.after(20000, mostrar_mensaje_temporal)

def iniciar_ciclo_mensaje():
    """Inicia el ciclo del mensaje temporal"""
    # Esperar 2 segundos después de que se inicie el programa y luego mostrar el primer mensaje
    ventana.after(2000, mostrar_mensaje_temporal)

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
    if not texto:
        return ""
    ancho_primera_linea = ancho_max - len(prefijo)
    lineas = []
    palabras = texto.split()
    linea_actual = []
    longitud_actual = 0

    for i, palabra in enumerate(palabras):
        if not lineas:
            ancho = ancho_primera_linea
        else:
            ancho = ancho_max
        espacio = 1 if linea_actual else 0
        if longitud_actual + len(palabra) + espacio <= ancho:
            linea_actual.append(palabra)
            longitud_actual += len(palabra) + espacio
        else:
            if linea_actual:
                if not lineas:
                    lineas.append(f"{prefijo}{' '.join(linea_actual)}")
                else:
                    indentacion = " " * len(prefijo)
                    lineas.append(f"{indentacion}{' '.join(linea_actual)}")
            linea_actual = [palabra]
            longitud_actual = len(palabra)

    if linea_actual:
        if not lineas:
            lineas.append(f"{prefijo}{' '.join(linea_actual)}")
        else:
            indentacion = " " * len(prefijo)
            lineas.append(f"{indentacion}{' '.join(linea_actual)}")

    return "\n".join(lineas)

def dividir_campo(texto, prefijo, ancho_max=32):
    if not texto:
        return prefijo
    ancho_primera_linea = ancho_max - len(prefijo)
    lineas = []
    palabras = texto.split()
    linea_actual = []
    longitud_actual = 0

    for i, palabra in enumerate(palabras):
        if not lineas:
            ancho = ancho_primera_linea
        else:
            ancho = ancho_max
        espacio = 1 if linea_actual else 0
        if longitud_actual + len(palabra) + espacio <= ancho:
            linea_actual.append(palabra)
            longitud_actual += len(palabra) + espacio
        else:
            if linea_actual:
                if not lineas:
                    lineas.append(f"{prefijo}{' '.join(linea_actual)}")
                else:
                    indentacion = " " * len(prefijo)
                    lineas.append(f"{indentacion}{' '.join(linea_actual)}")
            linea_actual = [palabra]
            longitud_actual = len(palabra)

    if linea_actual:
        if not lineas:
            lineas.append(f"{prefijo}{' '.join(linea_actual)}")
        else:
            indentacion = " " * len(prefijo)
            lineas.append(f"{indentacion}{' '.join(linea_actual)}")

    return "\n".join(lineas)

def mostrar_ventana_sabores(nombre, callback=None):
    global ventana_sabores
    if ventana_sabores:
        ventana_sabores.destroy()

    ventana_sabores = tk.Toplevel(ventana)
    ventana_sabores.title("Seleccionar Sabor")
    window_width = max(int(screen_width * 0.35), 400)  # Ventana un poco más ancha
    window_height = max(int(screen_height * 0.35), 300)  # Ventana más alta para botones cuadrados
    ventana_sabores.geometry(f"{window_width}x{window_height}")
    ventana_sabores.configure(bg="#e6d2a1")
    ventana_sabores.resizable(True, True)
    ventana_sabores.minsize(400, 300)

    tk.Label(ventana_sabores, text=f"Selecciona el sabor para {nombre}", 
             font=("Roboto", 14, "bold"), bg="#e6d2a1", fg="#3e2723").pack(pady=20, fill="x")

    # Frame para organizar los botones lado a lado (horizontalmente)
    frame_btn_sabores = tk.Frame(ventana_sabores, bg="#e6d2a1")
    frame_btn_sabores.pack(pady=20, fill="both", expand=True, padx=30)
    
    # Configurar grid para 1x2 (horizontal) con botones cuadrados
    frame_btn_sabores.grid_columnconfigure(0, weight=1)
    frame_btn_sabores.grid_columnconfigure(1, weight=1)
    frame_btn_sabores.grid_rowconfigure(0, weight=1)

    # Botón JAMAICA 
    btn_jamaica = tk.Button(frame_btn_sabores, text="JAMAICA", font=("Roboto", 14, "bold"), 
                            bg="#9c0000", fg="white", relief="flat", activebackground="#7a0000",
                            command=lambda: [callback("Jamaica") if callback else agregar_producto(nombre, "Jamaica"), ventana_sabores.destroy()])
    btn_jamaica.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
    btn_jamaica.bind("<Enter>", lambda e: btn_jamaica.config(bg="#7a0000"))
    btn_jamaica.bind("<Leave>", lambda e: btn_jamaica.config(bg="#9c0000"))

    # Botón HORCHATA 
    btn_horchata = tk.Button(frame_btn_sabores, text="HORCHATA", font=("Roboto", 14, "bold"), 
                             bg="#ffffff", fg="black", relief="flat", activebackground="#a8a4a4",
                             command=lambda: [callback("Horchata") if callback else agregar_producto(nombre, "Horchata"), ventana_sabores.destroy()])
    btn_horchata.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
    btn_horchata.bind("<Enter>", lambda e: btn_horchata.config(bg="#a8a4a4"))
    btn_horchata.bind("<Leave>", lambda e: btn_horchata.config(bg="#ffffff"))

    # Configurar para que los botones mantengan proporción cuadrada
    # El sticky="nsew" hace que se expandan para llenar todo el espacio disponible
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
    window_width = max(int(screen_width * 0.4), 400)
    window_height = max(int(screen_height * 0.3), 250)
    ventana_sabores.geometry(f"{window_width}x{window_height}")
    ventana_sabores.configure(bg="#e6d2a1")
    ventana_sabores.resizable(True, True)
    ventana_sabores.minsize(400, 250)

    tk.Label(ventana_sabores, text=f"Selecciona el tipo de {nombre}", 
             font=("Roboto", 12, "bold"), bg="#e6d2a1", fg="#3e2723").pack(pady=15, fill="x")

    # Frame para organizar los botones en 2x2
    frame_btn_refrescos = tk.Frame(ventana_sabores, bg="#e6d2a1")
    frame_btn_refrescos.pack(pady=10, fill="both", expand=True, padx=20)
    
    # Configurar grid para 2x2
    frame_btn_refrescos.grid_columnconfigure(0, weight=1)
    frame_btn_refrescos.grid_columnconfigure(1, weight=1)
    frame_btn_refrescos.grid_rowconfigure(0, weight=1)
    frame_btn_refrescos.grid_rowconfigure(1, weight=1)

    # Botón COCA (Rojo)
    btn_coca = tk.Button(frame_btn_refrescos, text="COCA", font=("Roboto", 11, "bold"), 
                         bg="#d32f2f", fg="white", relief="flat", activebackground="#b71c1c",
                         command=lambda: [callback("COCA") if callback else agregar_producto(nombre, "COCA"), ventana_sabores.destroy()])
    btn_coca.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
    btn_coca.bind("<Enter>", lambda e: btn_coca.config(bg="#b71c1c"))
    btn_coca.bind("<Leave>", lambda e: btn_coca.config(bg="#d32f2f"))

    # Botón FANTA (Naranja)
    btn_fanta = tk.Button(frame_btn_refrescos, text="FANTA", font=("Roboto", 11, "bold"), 
                          bg="#ff6f00", fg="white", relief="flat", activebackground="#ef6c00",
                          command=lambda: [callback("FANTA") if callback else agregar_producto(nombre, "FANTA"), ventana_sabores.destroy()])
    btn_fanta.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
    btn_fanta.bind("<Enter>", lambda e: btn_fanta.config(bg="#ef6c00"))
    btn_fanta.bind("<Leave>", lambda e: btn_fanta.config(bg="#ff6f00"))

    # Botón MANZA (Café MÁS CLARO - CAMBIO AQUÍ)
    btn_manza = tk.Button(frame_btn_refrescos, text="MANZA", font=("Roboto", 11, "bold"), 
                          bg="#9c4000", fg="white", relief="flat", activebackground="#8d6e63",
                          command=lambda: [callback("MANZA") if callback else agregar_producto(nombre, "MANZA"), ventana_sabores.destroy()])
    btn_manza.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
    btn_manza.bind("<Enter>", lambda e: btn_manza.config(bg="#8d6e63"))
    btn_manza.bind("<Leave>", lambda e: btn_manza.config(bg="#9c4000"))

    # Botón SPRITE (Verde)
    btn_sprite = tk.Button(frame_btn_refrescos, text="SPRITE", font=("Roboto", 11, "bold"), 
                           bg="#4caf50", fg="white", relief="flat", activebackground="#388e3c",
                           command=lambda: [callback("SPRITE") if callback else agregar_producto(nombre, "SPRITE"), ventana_sabores.destroy()])
    btn_sprite.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")
    btn_sprite.bind("<Enter>", lambda e: btn_sprite.config(bg="#388e3c"))
    btn_sprite.bind("<Leave>", lambda e: btn_sprite.config(bg="#4caf50"))

    ventana_sabores.protocol("WM_DELETE_WINDOW", lambda: ventana_sabores.destroy())

def mostrar_ventana_bebida_paquete(nombre_paquete):
    global ventana_sabores
    if ventana_sabores:
        ventana_sabores.destroy()

    ventana_sabores = tk.Toplevel(ventana)
    ventana_sabores.title(f"Seleccionar Bebida para {nombre_paquete}")
    window_width = max(int(screen_width * 0.35), 350)
    window_height = max(int(screen_height * 0.25), 200)
    ventana_sabores.geometry(f"{window_width}x{window_height}")
    ventana_sabores.configure(bg="#e6d2a1")
    ventana_sabores.resizable(True, True)
    ventana_sabores.minsize(350, 200)

    tk.Label(ventana_sabores, text=f"¿Qué bebida quieres con el {nombre_paquete}?", 
             font=("Roboto", 12, "bold"), bg="#e6d2a1", fg="#3e2723").pack(pady=15, fill="x")

    # Frame para organizar los botones horizontalmente
    frame_btn_bebidas = tk.Frame(ventana_sabores, bg="#e6d2a1")
    frame_btn_bebidas.pack(pady=10, fill="both", expand=True, padx=20)
    
    # Configurar grid para 1x2 (horizontal)
    frame_btn_bebidas.grid_columnconfigure(0, weight=1)
    frame_btn_bebidas.grid_columnconfigure(1, weight=1)
    frame_btn_bebidas.grid_rowconfigure(0, weight=1)

    # Botón REFRESCO (Azul)
    btn_refresco = tk.Button(frame_btn_bebidas, text="REFRESCO", font=("Roboto", 12, "bold"), 
                            bg="#2196f3", fg="white", relief="flat", activebackground="#1976d2",
                            command=lambda: [ventana_sabores.destroy(), seleccionar_refresco_paquete(nombre_paquete)])
    btn_refresco.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    btn_refresco.bind("<Enter>", lambda e: btn_refresco.config(bg="#1976d2"))
    btn_refresco.bind("<Leave>", lambda e: btn_refresco.config(bg="#2196f3"))

    # Botón AGUA FRESCA (Verde)
    btn_agua = tk.Button(frame_btn_bebidas, text="AGUA FRESCA\n(+$5)", font=("Roboto", 12, "bold"), 
                        bg="#4caf50", fg="white", relief="flat", activebackground="#388e3c",
                        command=lambda: [ventana_sabores.destroy(), seleccionar_agua_paquete(nombre_paquete)])
    btn_agua.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    btn_agua.bind("<Enter>", lambda e: btn_agua.config(bg="#388e3c"))
    btn_agua.bind("<Leave>", lambda e: btn_agua.config(bg="#4caf50"))

    ventana_sabores.protocol("WM_DELETE_WINDOW", lambda: ventana_sabores.destroy())

def seleccionar_refresco_paquete(nombre_paquete):
    """Función para manejar la selección de refresco en paquetes"""
    def callback_refresco(tipo_refresco):
        # Proceder directamente a agregar el producto con el refresco seleccionado
        agregar_producto(nombre_paquete, tipo_refresco)
    
    mostrar_ventana_refrescos("refresco", callback=callback_refresco)

def seleccionar_agua_paquete(nombre_paquete):
    """Función para manejar la selección de agua fresca en paquetes"""
    def callback_agua(sabor_agua):
        # Agregar el paquete con agua fresca (+$5) y el sabor seleccionado
        agregar_producto_paquete_agua(nombre_paquete, f"agua fresca {sabor_agua}")
    
    mostrar_ventana_sabores("agua fresca", callback=callback_agua)

def agregar_producto_paquete_agua(nombre, sabor_agua):
    """Función específica para agregar paquetes con agua fresca"""
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos:
            grupos.append("General")

    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({
            "nombre": "Envío",
            "anotacion": None,
            "precio": 15,
            "grupo": "General",
            "cantidad": 1
        })

    # El precio base + $5 por agua fresca
    precio_base = menu_productos[nombre] + 5

    ventana_item = tk.Toplevel(ventana)
    ventana_item.title(f"Agregar {nombre}")
    ventana_item.geometry("400x280")
    ventana_item.configure(bg="#e6d2a1")

    tk.Label(ventana_item, text="Cantidad:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=8)
    cantidad_entry = tk.Entry(ventana_item, font=("Roboto", 12), width=20)
    cantidad_entry.insert(0, "1")
    cantidad_entry.pack(pady=8)

    tk.Label(ventana_item, text="Nota:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=8)
    nota_entry = tk.Entry(ventana_item, font=("Roboto", 12), width=30)
    nota_entry.pack(pady=8)

    def confirmar():
        try:
            cantidad = int(cantidad_entry.get())
            if cantidad <= 0:
                raise ValueError("Cantidad debe ser mayor a 0.")
            nota_adicional = nota_entry.get()
            
            # Combinar sabor de agua y nota adicional
            if sabor_agua and nota_adicional:
                anotacion_final = f"{sabor_agua}, {nota_adicional}"
            elif sabor_agua:
                anotacion_final = sabor_agua
            elif nota_adicional:
                anotacion_final = nota_adicional
            else:
                anotacion_final = sabor_agua
                
            precio_final = precio_base * cantidad

            item = {
                "nombre": nombre,
                "anotacion": anotacion_final,
                "precio": precio_final,
                "grupo": grupo_actual,
                "cantidad": cantidad
            }
            pedido_actual.append(item)
            ventana_item.destroy()
            actualizar_ticket()

        except ValueError as e:
            messagebox.showerror("Error", f"Entrada inválida: {e}", parent=ventana_item)

    tk.Button(ventana_item, text="Confirmar", font=("Roboto", 12), bg="#4caf50", fg="white", 
              command=confirmar, width=15, pady=5).pack(pady=15)
    
    # CAMBIO CLAVE: QUITAR grab_set() para que el botón de teclado funcione
    ventana_item.transient(ventana)
    # ventana_item.grab_set()  # COMENTADO: Esto bloqueaba el botón de teclado

def agregar_carne_gramos():
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos:
            grupos.append("General")

    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({
            "nombre": "Envío",
            "anotacion": None,
            "precio": 15,
            "grupo": "General",
            "cantidad": 1
        })

    ventana_carne = tk.Toplevel(ventana)
    ventana_carne.title("Carne(Gramos)")
    ventana_carne.geometry("400x280")
    ventana_carne.configure(bg="#e6d2a1")

    tk.Label(ventana_carne, text="Gramos:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=8)
    gramos_entry = tk.Entry(ventana_carne, font=("Roboto", 12), width=20)
    gramos_entry.pack(pady=8)

    tk.Label(ventana_carne, text="O Monto ($):", font=("Roboto", 12), bg="#e6d2a1").pack(pady=8)
    dinero_entry = tk.Entry(ventana_carne, font=("Roboto", 12), width=20)
    dinero_entry.pack(pady=8)

    def confirmar():
        try:
            gramos_str = gramos_entry.get().strip()
            dinero_str = dinero_entry.get().strip()
            precio_kilo = 300
            precio_por_gramo = 0.3

            if not gramos_str and not dinero_str:
                messagebox.showerror("Error", "Debe ingresar gramos o monto.", parent=ventana_carne)
                return
            if gramos_str and dinero_str:
                messagebox.showerror("Error", "Ingrese solo un campo: gramos o monto.", parent=ventana_carne)
                return

            if gramos_str:
                gramos = float(gramos_str)
                if gramos <= 0:
                    raise ValueError("Gramos debe ser positivo.")
                precio_final = gramos * precio_por_gramo
                gramos_final = gramos
            else:
                dinero = float(dinero_str)
                if dinero <= 0:
                    raise ValueError("Monto debe ser positivo.")
                gramos_final = dinero / precio_por_gramo
                precio_final = dinero

            ventana_carne.destroy()
            anotacion = simpledialog.askstring("Anotación", "Alguna nota para Carne(Gramos)? (Ej. bien cocida)", parent=ventana)
            if anotacion:
                anotacion = f"{gramos_final:.2f}g, {anotacion}"
            else:
                anotacion = f"{gramos_final:.2f}g"

            item = {
                "nombre": "Carne(Gramos)",
                "anotacion": anotacion,
                "precio": round(precio_final, 2),
                "grupo": grupo_actual,
                "cantidad": 1
            }
            pedido_actual.append(item)
            actualizar_ticket()

        except ValueError as e:
            messagebox.showerror("Error", f"Entrada inválida: {e}", parent=ventana_carne)

    tk.Button(ventana_carne, text="Confirmar", font=("Roboto", 12), bg="#4caf50", fg="white", 
              command=confirmar, width=15, pady=5).pack(pady=15)
    
    # CAMBIO CLAVE: QUITAR grab_set() para que el botón de teclado funcione
    ventana_carne.transient(ventana)
    # ventana_carne.grab_set()  # COMENTADO: Esto bloqueaba el botón de teclado

def agregar_nuevo_item():
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos:
            grupos.append("General")

    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({
            "nombre": "Envío",
            "anotacion": None,
            "precio": 15,
            "grupo": "General",
            "cantidad": 1
        })

    nombre = simpledialog.askstring("Nuevo Ítem", "Ingresa el nombre del nuevo ítem:", parent=ventana)
    if not nombre:
        return

    precio = simpledialog.askfloat("Precio", f"Ingresa el precio para {nombre}:", minvalue=0, parent=ventana)
    if precio is None:
        return

    anotacion = simpledialog.askstring("Anotación", f"Alguna nota para {nombre}?", parent=ventana)
    if nombre and precio is not None:
        item = {
            "nombre": nombre,
            "anotacion": anotacion,
            "precio": precio,
            "grupo": grupo_actual,
            "cantidad": 1
        }
        pedido_actual.append(item)
        actualizar_ticket()

def agregar_descuento():
    global grupo_actual
    if grupo_actual is None:
        grupo_actual = "General"
        if "General" not in grupos:
            grupos.append("General")

    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({
            "nombre": "Envío",
            "anotacion": None,
            "precio": 15,
            "grupo": "General",
            "cantidad": 1
        })

    monto = simpledialog.askfloat("Descuento", "Ingresa el monto del descuento:", minvalue=0, parent=ventana)
    if monto is None:
        return

    anotacion = simpledialog.askstring("Nota del Descuento", "Ingresa una nota para el descuento (opcional):", parent=ventana)

    item = {
        "nombre": f"Descuento",
        "anotacion": anotacion,
        "precio": -monto,
        "grupo": grupo_actual,
        "cantidad": 1
    }
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
        with open(clave_archivo, "w") as f:
            f.write("123")
    with open(clave_archivo, "r") as f:
        clave_guardada = f.read().strip()

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
        if "General" not in grupos:
            grupos.append("General")

    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({
            "nombre": "Envío",
            "anotacion": None,
            "precio": 15,
            "grupo": "General",
            "cantidad": 1
        })

    precio_base = menu_productos[nombre]
    anotacion = sabor

    ventana_item = tk.Toplevel(ventana)
    ventana_item.title(f"Agregar {nombre}")
    ventana_item.geometry("400x280")
    ventana_item.configure(bg="#e6d2a1")

    tk.Label(ventana_item, text="Cantidad:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=8)
    cantidad_entry = tk.Entry(ventana_item, font=("Roboto", 12), width=20)
    cantidad_entry.insert(0, "1")
    cantidad_entry.pack(pady=8)

    tk.Label(ventana_item, text="Nota:", font=("Roboto", 12), bg="#e6d2a1").pack(pady=8)
    nota_entry = tk.Entry(ventana_item, font=("Roboto", 12), width=30)
    nota_entry.pack(pady=8)

    def confirmar():
        try:
            cantidad = int(cantidad_entry.get())
            if cantidad <= 0:
                raise ValueError("Cantidad debe ser mayor a 0.")
            nota_adicional = nota_entry.get()
            
            # Combinar sabor y nota adicional
            if sabor and nota_adicional:
                anotacion_final = f"{sabor}, {nota_adicional}"
            elif sabor:
                anotacion_final = sabor
            elif nota_adicional:
                anotacion_final = nota_adicional
            else:
                anotacion_final = None
                
            precio_final = precio_base * cantidad

            item = {
                "nombre": nombre,
                "anotacion": anotacion_final,
                "precio": precio_final,
                "grupo": grupo_actual,
                "cantidad": cantidad
            }
            pedido_actual.append(item)
            ventana_item.destroy()
            actualizar_ticket()

        except ValueError as e:
            messagebox.showerror("Error", f"Entrada inválida: {e}", parent=ventana_item)

    tk.Button(ventana_item, text="Confirmar", font=("Roboto", 12), bg="#4caf50", fg="white", 
              command=confirmar, width=15, pady=5).pack(pady=15)
    
    # CAMBIO CLAVE: QUITAR grab_set() para que el botón de teclado funcione
    ventana_item.transient(ventana)
    # ventana_item.grab_set()  # COMENTADO: Esto bloqueaba el botón de teclado

def crear_grupo():
    global grupo_actual
    nombre = simpledialog.askstring("Nuevo grupo", "Nombre del grupo (ej. Ana):", parent=ventana)
    if nombre:
        grupo_actual = nombre
        if nombre not in grupos:
            grupos.append(nombre)
        actualizar_ticket()

def actualizar_ticket():
    for widget in frame_resumen.winfo_children():
        widget.destroy()

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
            tk.Label(columna_actual, text=f"Grupo: {grupo}", font=("Roboto", 12, "bold"), anchor="w", bg="#ffffff", fg="#3e2723").pack(anchor="w", pady=5)

            tk.Label(columna_actual, text="Producto          | Cantidad | Precio", font=("Roboto", 11, "bold"), anchor="w", bg="#ffffff", fg="#3e2723").pack(anchor="w")
            tk.Label(columna_actual, text="-" * 40, font=("Roboto", 11), anchor="w", bg="#ffffff", fg="#3e2723").pack(anchor="w")

            for item in items_agrupados[grupo]:
                producto = item["nombre"][:18].ljust(18)
                cantidad = str(item["cantidad"]).center(8)
                precio = f"${item['precio']:.2f}".rjust(10)
                texto = f"{producto} | {cantidad} | {precio}"
                if item["anotacion"]:
                    texto += f"\n{dividir_texto(item['anotacion'])}"

                fila = tk.Frame(columna_actual, bg="#ffffff")
                fila.pack(fill="x", pady=3)

                tk.Label(fila, text=texto, anchor="w", justify="left", bg="#ffffff", font=("Roboto", 11), fg="#3e2723").pack(side="left", fill="x", expand=True)
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

def guardar_en_historial(fecha_hora, domicilio, total):
    hoy = date.today().isoformat()
    telefono = entry_telefono.get().strip()
    cruces = entry_cruces.get().strip()
    
    items_copy = copy.deepcopy(pedido_actual)
    
    with open(f"historial_{hoy}.txt", "a", encoding="utf-8") as f:
        f.write(f"===== PEDIDO - {fecha_hora} =====\n")
        f.write(f"Fecha y Hora: {fecha_hora}\n")
        f.write(f"Domicilio: {domicilio.strip()}\n")
        f.write(f"Teléfono: {telefono}\n")
        f.write(f"Cruces: {cruces}\n")
        if hora_especifica:
            f.write(f"Hora Específica: {hora_especifica.strip()}\n")
        f.write("--- Productos ---\n")

        items_agrupados = {}
        for item in items_copy:
            grupo = item.get("grupo", "General")
            items_agrupados.setdefault(grupo, []).append(item)

        for grupo in sorted(items_agrupados.keys(), key=lambda x: (x == "General", x)):
            f.write(f"\nCliente: {grupo.upper()}\n")
            for item in items_agrupados[grupo]:
                f.write(f"  - {item['nombre']} (x{item['cantidad']}) (${item['precio']:.2f})\n")
                if item['anotacion']:
                    f.write(dividir_texto(item['anotacion'], 32, "    Nota: ") + "\n")

        f.write(f"\nTotal: ${total:.2f}\n")
        f.write("=" * 35  + "\n\n")
    
    print(f"[SAVE] Guardado en historial: {len(pedido_actual)} productos, Total: ${total:.2f}")

# ========== FUNCIONES CORREGIDAS PARA IMPRESIÓN ==========

def verificar_impresora():
    """Verifica si hay una impresora disponible y configurada"""
    try:
        printer_name = win32print.GetDefaultPrinter()
        if not printer_name:
            return False, "No se encontró una impresora predeterminada. Configura una en el sistema."
        
        # Verificar si la impresora está disponible
        printers = win32print.EnumPrinters(2)
        printer_encontrada = False
        for printer in printers:
            if printer[2] == printer_name:
                printer_encontrada = True
                break
        
        if not printer_encontrada:
            return False, f"La impresora '{printer_name}' no está disponible."
        
        return True, printer_name
        
    except Exception as e:
        return False, f"Error al verificar la impresora: {str(e)}"

def imprimir_texto(texto, doc_name="Documento"):
    """Función mejorada para imprimir con mejor manejo de errores"""
    try:
        # Verificar impresora primero
        impresora_ok, resultado = verificar_impresora()
        if not impresora_ok:
            messagebox.showerror("Error de Impresora", resultado)
            return False
        
        printer_name = resultado
        print(f"[PRINT] Intentando imprimir en: {printer_name}")
        
        # Abrir impresora
        hprinter = win32print.OpenPrinter(printer_name)
        
        # Crear contexto de dispositivo
        hdc = win32ui.CreateDC()
        try:
            hdc.CreatePrinterDC(printer_name)
        except win32ui.error as e:
            messagebox.showerror("Error", f"No se pudo crear el contexto de dispositivo: {str(e)}")
            win32print.ClosePrinter(hprinter)
            return False
        
        # Iniciar documento
        hdc.StartDoc(doc_name)
        hdc.StartPage()

        # Configurar fuente
        try:
            font = win32ui.CreateFont({
                "name": "Arial",
                "height": 30,
                "weight": FW_NORMAL
            })
            hdc.SelectObject(font)
        except win32ui.error as e:
            messagebox.showerror("Error", f"No se pudo configurar la fuente: {str(e)}")
            hdc.EndPage()
            hdc.EndDoc()
            win32print.ClosePrinter(hprinter)
            return False

        # Imprimir líneas
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

        # Finalizar
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

def imprimir_ticket_personalizado(fecha, domicilio, telefono, cruces, total, items):
    """Función mejorada para generar el ticket"""
    global hora_especifica
    
    try:
        ticket = f"{centrar('TORTAS AHOGADAS')}\n"
        ticket += f"{centrar('DOÑA SUSY')}\n"
        ticket += f"{centrar('Geranio #869A')}\n"
        ticket += f"{centrar('Col.Tulipanes CP:45647')}\n"
        ticket += f"{centrar('33-3684-4525')}\n"
        ticket += "=" * 32 + "\n"
        ticket += dividir_campo(domicilio, "Domicilio: ") + "\n"
        ticket += dividir_campo(telefono, "Telefono: ") + "\n"
        ticket += dividir_campo(cruces, "Cruces: ") + "\n"
        ticket += f"Fecha: {fecha}\n"
        if hora_especifica:
            ticket += f"Hora especifica: {hora_especifica}\n"
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
                if item['anotacion']:
                    ticket += dividir_texto(item['anotacion']) + "\n"
            ticket += "=================================\n"

        ticket += "=" * 32 + "\n"
        ticket += f"{centrar(f'TOTAL: ${total:.2f}')}\n"
        ticket += f"{centrar('Gracias por su pedido')}\n"
        ticket += "=" * 32 + "\n"

        # Contar bebidas del pedido
        refrescos = {}  # {tipo: cantidad}
        aguas_frescas = {}  # {sabor_tamaño: cantidad}
        
        for item in items:
            nombre = item["nombre"]
            cantidad = item["cantidad"]
            anotacion = item.get("anotacion", "") or ""
            
            # Refresco directo
            if nombre == "Refresco":
                tipo_refresco = anotacion.split(",")[0].strip() if anotacion else "Sin especificar"
                refrescos[tipo_refresco] = refrescos.get(tipo_refresco, 0) + cantidad
            
            # Paquetes con refresco o agua fresca
            elif nombre in ["Paquete 1", "Paquete 2"]:
                if "agua fresca" in anotacion.lower():
                    # Es agua fresca en paquete
                    if "agua fresca jamaica" in anotacion.lower():
                        aguas_frescas["Jamaica (Paquete)"] = aguas_frescas.get("Jamaica (Paquete)", 0) + cantidad
                    elif "agua fresca horchata" in anotacion.lower():
                        aguas_frescas["Horchata (Paquete)"] = aguas_frescas.get("Horchata (Paquete)", 0) + cantidad
                    else:
                        aguas_frescas["Sin especificar (Paquete)"] = aguas_frescas.get("Sin especificar (Paquete)", 0) + cantidad
                else:
                    # Es refresco en paquete
                    for tipo in ["COCA", "FANTA", "MANZA", "SPRITE"]:
                        if tipo in anotacion:
                            refrescos[tipo] = refrescos.get(tipo, 0) + cantidad
                            break
                    else:
                        # Si no se encontró tipo específico pero no es agua fresca
                        if anotacion and "agua fresca" not in anotacion.lower():
                            tipo_refresco = anotacion.split(",")[0].strip()
                            refrescos[tipo_refresco] = refrescos.get(tipo_refresco, 0) + cantidad
            
            # Aguas chicas/grandes
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
        
        # Agregar resumen de bebidas si hay alguna
        if refrescos or aguas_frescas:
            if refrescos:
                ticket += f"{centrar('RESUMEN DE REFRESCOS:')}\n"
                for tipo, cant in refrescos.items():
                    ticket += f"{centrar(f'{tipo}: {cant}')}\n"
            
            if aguas_frescas:
                ticket += f"{centrar('RESUMEN DE AGUAS FRESCAS:')}\n"
                for sabor, cant in aguas_frescas.items():
                    ticket += f"{centrar(f'{sabor}: {cant}')}\n"
            
            ticket += "=" * 32

        return ticket
        
    except Exception as e:
        print(f"[ERROR] Error generando ticket: {e}")
        return f"Error generando ticket: {str(e)}"

# ========== FUNCIONES PARA EVITAR TICKETS DUPLICADOS - CORREGIDAS ==========

def obtener_ultimo_ticket_guardado():
    """Obtiene la información del último ticket guardado en el historial - MEJORADA"""
    hoy = date.today().isoformat()
    archivo = f"historial_{hoy}.txt"
    
    if not os.path.exists(archivo):
        print("[DEBUG] No existe archivo de historial")
        return None
    
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
        
        if not contenido:
            print("[DEBUG] Archivo de historial vacio")
            return None
            
        # Dividir por pedidos y tomar el último
        pedidos = contenido.split("===== PEDIDO - ")[1:]
        if not pedidos:
            print("[DEBUG] No se encontraron pedidos en el historial")
            return None
            
        ultimo_pedido = pedidos[-1]
        lineas = ultimo_pedido.strip().split("\n")
        
        print(f"[DEBUG] Procesando ultimo pedido con {len(lineas)} lineas")
        
        # Extraer información del último pedido
        ultimo_ticket = {
            "domicilio": "",
            "telefono": "",
            "cruces": "",
            "hora_especifica": None,
            "items": [],
            "total": 0
        }
        
        grupo_actual = None
        
        for i, linea in enumerate(lineas[1:], 1):  # Saltar la primera línea que es la fecha
            linea = linea.strip()  # Limpiar espacios
            print(f"[DEBUG] Linea {i}: '{linea}'")
            
            if linea.startswith("Domicilio:"):
                ultimo_ticket["domicilio"] = linea.replace("Domicilio:", "").strip()
                print(f"[DEBUG] Domicilio extraido: '{ultimo_ticket['domicilio']}'")
            elif linea.startswith("Teléfono:"):
                ultimo_ticket["telefono"] = linea.replace("Teléfono:", "").strip()
                print(f"[DEBUG] Telefono extraido: '{ultimo_ticket['telefono']}'")
            elif linea.startswith("Cruces:"):
                ultimo_ticket["cruces"] = linea.replace("Cruces:", "").strip()
                print(f"[DEBUG] Cruces extraido: '{ultimo_ticket['cruces']}'")
            elif linea.startswith("Hora Específica:"):
                hora_str = linea.replace("Hora Específica:", "").strip()
                ultimo_ticket["hora_especifica"] = hora_str if hora_str else None
                print(f"[DEBUG] Hora especifica extraida: '{ultimo_ticket['hora_especifica']}'")
            elif linea.startswith("Cliente:"):
                grupo_actual = linea.replace("Cliente:", "").strip()
                print(f"[DEBUG] Grupo extraido: '{grupo_actual}'")
            elif linea.startswith("  - "):
                # Extraer información del producto
                producto_linea = linea.replace("  - ", "").strip()
                print(f"[DEBUG] Procesando producto: '{producto_linea}'")
                try:
                    if "(x" in producto_linea and ") ($" in producto_linea:
                        # Formato: "Producto (x2) ($50.00)"
                        nombre = producto_linea.split(" (x")[0].strip()
                        resto = producto_linea.split(" (x")[1]
                        cantidad = int(resto.split(") ($")[0])
                        precio = float(resto.split(") ($")[1].replace(")", ""))
                    else:
                        # Formato sin cantidad explícita: "Producto ($25.00)"
                        nombre = producto_linea.split(" ($")[0].strip()
                        precio = float(producto_linea.split(" ($")[1].replace(")", ""))
                        cantidad = 1
                    
                    item = {
                        "nombre": nombre,
                        "cantidad": cantidad,
                        "precio": precio,
                        "grupo": grupo_actual or "General",
                        "anotacion": None
                    }
                    ultimo_ticket["items"].append(item)
                    print(f"[DEBUG] Item agregado: {item}")
                except (ValueError, IndexError) as e:
                    print(f"[ERROR] Error procesando linea de producto: {producto_linea} - {e}")
                    continue
            elif linea.startswith("    Nota:") and ultimo_ticket["items"]:
                # Agregar nota al último item
                nota = linea.replace("    Nota:", "").strip()
                if ultimo_ticket["items"][-1]["anotacion"]:
                    ultimo_ticket["items"][-1]["anotacion"] += " " + nota
                else:
                    ultimo_ticket["items"][-1]["anotacion"] = nota
                print(f"[DEBUG] Nota agregada al ultimo item: '{nota}'")
            elif linea.startswith("Total:"):
                total_str = linea.replace("Total:", "").replace("$", "").strip()
                ultimo_ticket["total"] = float(total_str)
                print(f"[DEBUG] Total extraido: {ultimo_ticket['total']}")
        
        print(f"[DEBUG] Ultimo ticket leido: {len(ultimo_ticket['items'])} productos, Total: ${ultimo_ticket['total']:.2f}")
        print(f"[DEBUG] Items extraidos: {ultimo_ticket['items']}")
        return ultimo_ticket
        
    except Exception as e:
        print(f"[ERROR] Error al leer ultimo ticket: {e}")
        import traceback
        traceback.print_exc()
        return None

def tickets_son_iguales(ticket_actual, ultimo_ticket):
    """Compara si dos tickets son idénticos - VERSION SIMPLIFICADA Y ROBUSTA"""
    if ultimo_ticket is None:
        print("[DEBUG] No hay ticket anterior para comparar")
        return False
    
    print("[DEBUG] === COMPARANDO TICKETS ===")
    
    # 1. Comparar datos básicos del cliente
    print(f"[DEBUG] Comparando domicilio: '{ticket_actual['domicilio']}' vs '{ultimo_ticket['domicilio']}'")
    if ticket_actual["domicilio"].strip() != ultimo_ticket["domicilio"].strip():
        print("[DEBUG] Domicilios diferentes")
        return False
        
    print(f"[DEBUG] Comparando telefono: '{ticket_actual['telefono']}' vs '{ultimo_ticket['telefono']}'")
    if ticket_actual["telefono"].strip() != ultimo_ticket["telefono"].strip():
        print("[DEBUG] Telefonos diferentes")
        return False
        
    print(f"[DEBUG] Comparando cruces: '{ticket_actual['cruces']}' vs '{ultimo_ticket['cruces']}'")
    if ticket_actual["cruces"].strip() != ultimo_ticket["cruces"].strip():
        print("[DEBUG] Cruces diferentes")
        return False
    
    # 2. Comparar total
    print(f"[DEBUG] Comparando total: {ticket_actual['total']} vs {ultimo_ticket['total']}")
    if abs(ticket_actual["total"] - ultimo_ticket["total"]) > 0.01:
        print("[DEBUG] Totales diferentes")
        return False
    
    # 3. Comparar cantidad de productos
    print(f"[DEBUG] Comparando cantidad productos: {len(ticket_actual['items'])} vs {len(ultimo_ticket['items'])}")
    if len(ticket_actual["items"]) != len(ultimo_ticket["items"]):
        print("[DEBUG] Cantidad de productos diferente")
        return False
    
    # 4. Comparar productos de forma simple
    print("[DEBUG] Comparando productos...")
    
    # Crear listas simples para comparar
    productos_actual = []
    productos_ultimo = []
    
    for item in ticket_actual["items"]:
        producto_str = f"{item['nombre']}|{item['cantidad']}|{item['precio']:.2f}|{item.get('grupo', 'General')}|{item.get('anotacion', '') or ''}"
        productos_actual.append(producto_str)
        print(f"[DEBUG] Producto actual: {producto_str}")
    
    for item in ultimo_ticket["items"]:
        producto_str = f"{item['nombre']}|{item['cantidad']}|{item['precio']:.2f}|{item.get('grupo', 'General')}|{item.get('anotacion', '') or ''}"
        productos_ultimo.append(producto_str)
        print(f"[DEBUG] Producto ultimo: {producto_str}")
    
    # Ordenar ambas listas para comparar
    productos_actual.sort()
    productos_ultimo.sort()
    
    print(f"[DEBUG] Productos actual ordenados: {productos_actual}")
    print(f"[DEBUG] Productos ultimo ordenados: {productos_ultimo}")
    
    if productos_actual != productos_ultimo:
        print("[DEBUG] Productos diferentes")
        return False
    
    print("[SUCCESS] *** TICKETS IDENTICOS DETECTADOS ***")
    return True

def debug_comparacion_tickets(ticket_actual, ultimo_ticket):
    """Función de debug para ver las diferencias entre tickets"""
    print("\n" + "="*50)
    print("[DEBUG] COMPARACION DE TICKETS")
    print("="*50)
    
    if ultimo_ticket is None:
        print("[ERROR] No hay ticket anterior para comparar")
        return
    
    print("[TICKET ACTUAL]:")
    print(f"   Domicilio: '{ticket_actual['domicilio']}'")
    print(f"   Telefono: '{ticket_actual['telefono']}'")
    print(f"   Cruces: '{ticket_actual['cruces']}'")
    print(f"   Hora especifica: '{ticket_actual['hora_especifica']}'")
    print(f"   Total: {ticket_actual['total']}")
    print(f"   Productos: {len(ticket_actual['items'])}")
    
    print("\n[ULTIMO TICKET GUARDADO]:")
    print(f"   Domicilio: '{ultimo_ticket['domicilio']}'")
    print(f"   Telefono: '{ultimo_ticket['telefono']}'")
    print(f"   Cruces: '{ultimo_ticket['cruces']}'")
    print(f"   Hora especifica: '{ultimo_ticket['hora_especifica']}'")
    print(f"   Total: {ultimo_ticket['total']}")
    print(f"   Productos: {len(ultimo_ticket['items'])}")
    
    # Comparar productos detalladamente
    print("\n[COMPARACION DE PRODUCTOS]:")
    
    if len(ticket_actual["items"]) != len(ultimo_ticket["items"]):
        print(f"   [DIFERENTE] Cantidad productos: {len(ticket_actual['items'])} vs {len(ultimo_ticket['items'])}")
        return
    
    def ordenar_key(x):
        return (x["nombre"], x["grupo"] or "General", x["anotacion"] or "", x["cantidad"])
    
    items_actual = sorted(ticket_actual["items"], key=ordenar_key)
    items_ultimo = sorted(ultimo_ticket["items"], key=ordenar_key)
    
    productos_iguales = True
    for i, (item_actual, item_ultimo) in enumerate(zip(items_actual, items_ultimo)):
        print(f"\n   Producto {i+1}:")
        print(f"     ACTUAL:  {item_actual}")
        print(f"     ULTIMO:  {item_ultimo}")
        
        # Normalizar anotaciones para comparación
        anotacion_actual = (item_actual["anotacion"] or "").strip()
        anotacion_ultimo = (item_ultimo["anotacion"] or "").strip()
        
        if (item_actual["nombre"].strip() != item_ultimo["nombre"].strip() or
            item_actual["cantidad"] != item_ultimo["cantidad"] or
            abs(item_actual["precio"] - item_ultimo["precio"]) > 0.01 or
            (item_actual["grupo"] or "General") != (item_ultimo["grupo"] or "General") or
            anotacion_actual != anotacion_ultimo):
            print("     [DIFERENTES]")
            productos_iguales = False
        else:
            print("     [IGUALES]")
    
    print(f"\n[RESULTADO FINAL]: {'TICKETS IDENTICOS' if productos_iguales else 'TICKETS DIFERENTES'}")
    print("="*50 + "\n")

def imprimir_ticket():
    """Función CORREGIDA para imprimir ticket con detección anti-duplicados robusta"""
    try:
        print("[PRINT] === INICIANDO PROCESO DE IMPRESION ===")
        
        # 1. VALIDAR DATOS BÁSICOS
        domicilio = entry_domicilio.get().strip()
        telefono = entry_telefono.get().strip()
        cruces = entry_cruces.get().strip()

        if not domicilio or not telefono or not cruces:
            messagebox.showwarning("Faltan datos", "Debes llenar domicilio, teléfono y cruces.")
            return

        # 2. VALIDAR QUE HAY PRODUCTOS
        if not pedido_actual:
            messagebox.showwarning("Sin productos", "Agrega al menos un producto antes de imprimir.")
            return

        print(f"[PRINT] Datos del cliente: Domicilio='{domicilio}', Telefono='{telefono}', Cruces='{cruces}'")
        print(f"[PRINT] Productos en pedido: {len(pedido_actual)}")

        # 3. GENERAR DATOS DEL TICKET
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")
        total = sum(item['precio'] for item in pedido_actual)
        items_copy = copy.deepcopy(pedido_actual)

        print(f"[PRINT] Total calculado: ${total:.2f}")

        # 4. PREPARAR DATOS PARA COMPARACIÓN ANTI-DUPLICADOS
        ticket_actual = {
            "domicilio": domicilio,
            "telefono": telefono,
            "cruces": cruces,
            "hora_especifica": hora_especifica.strip() if hora_especifica else None,
            "items": items_copy,
            "total": total
        }

        print(f"[PRINT] Ticket actual preparado: {ticket_actual}")

        # 5. VERIFICAR DUPLICADOS
        print("[PRINT] === VERIFICANDO DUPLICADOS ===")
        ultimo_ticket = obtener_ultimo_ticket_guardado()
        
        if ultimo_ticket:
            print("[PRINT] Se encontro un ticket previo, comparando...")
            es_duplicado = tickets_son_iguales(ticket_actual, ultimo_ticket)
        else:
            print("[PRINT] No hay tickets previos, este sera el primero")
            es_duplicado = False

        # 6. GUARDAR CLIENTE (SIEMPRE)
        print("[PRINT] Guardando datos del cliente...")
        guardar_actualizar_cliente(telefono, domicilio, cruces)

        # 7. MANEJAR DUPLICADOS
        if es_duplicado:
            print("[WARNING] *** TICKET DUPLICADO DETECTADO ***")
            respuesta = messagebox.askyesno(
                "Ticket Duplicado Detectado", 
                "Este ticket es identico al anterior.\n\n¿Deseas imprimir de todas formas?\n\n(No se guardara en el historial)",
                icon="warning"
            )
            if not respuesta:
                print("[CANCEL] Usuario cancelo la impresion del duplicado")
                return
            else:
                print("[PRINT] Usuario confirmo imprimir duplicado")
        else:
            print("[PRINT] Ticket nuevo, guardando en historial...")
            guardar_en_historial(fecha_hora, domicilio, total)
            print("[SUCCESS] Ticket guardado en historial")

        # 8. GENERAR TICKET PARA IMPRESIÓN
        print("[PRINT] Generando contenido del ticket...")
        ticket_contenido = imprimir_ticket_personalizado(fecha_hora, domicilio, telefono, cruces, total, items_copy)
        
        if "Error generando ticket" in ticket_contenido:
            messagebox.showerror("Error", "No se pudo generar el contenido del ticket.")
            return

        # 9. IMPRIMIR TICKET
        print("[PRINT] Enviando a impresora...")
        resultado_impresion = imprimir_texto(ticket_contenido, "Ticket")
        
        if resultado_impresion:
            print("[SUCCESS] === IMPRESION COMPLETADA EXITOSAMENTE ===")
        else:
            print("[ERROR] === ERROR EN LA IMPRESION ===")

    except Exception as e:
        error_msg = f"Error inesperado en imprimir_ticket: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", error_msg)

# ========== FIN FUNCIONES ANTI-DUPLICADOS CORREGIDAS ==========

def imprimir_ticket_directo(ticket_texto):
    imprimir_texto(ticket_texto, "Ticket")

def imprimir_ticket_personalizado_2(fecha, domicilio, total, items):
    global hora_especifica
    ticket = f"{centrar('TORTAS AHOGADAS DOÑA SUSY')}\n"
    ticket += "=" * 32 + "\n"
    ticket += dividir_campo(domicilio, "Domicilio: ") + "\n"
    ticket += f"Fecha: {fecha}\n"
    if hora_especifica:
        ticket += f"Hora específica: {hora_especifica}\n"
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
            if item['anotacion']:
                ticket += dividir_texto(item['anotacion']) + "\n"
        ticket += "=================================\n"

    ticket += "=" * 32 + "\n"
    ticket += f"{centrar(f'TOTAL: ${total:.2f}')}\n"
    ticket += "=" * 32

    return ticket

def mostrar_resumen_dia():
    clave_archivo = "clave.txt"
    if not os.path.exists(clave_archivo):
        with open(clave_archivo, "w") as f:
            f.write("123")
    with open(clave_archivo, "r") as f:
        clave_guardada = f.read().strip()

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
        with open(archivo, "r", encoding="utf-8") as f:
            contenido = f.read().strip().split("===== PEDIDO - ")[1:]
        if 0 <= indice < len(contenido):
            contenido.pop(indice)
            with open(archivo, "w", encoding="utf-8") as f:
                for i, pedido in enumerate(contenido, 1):
                    f.write(f"===== PEDIDO - {pedido.split('\n')[0]} =====\n")
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

    # Header
    header_frame = tk.Frame(ventana_resumen, bg="#4caf50", height=70)
    header_frame.pack(fill="x", pady=(0, 15))
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="📊 Resumen del Día", 
             font=("Roboto", 18, "bold"), bg="#4caf50", fg="white").pack(expand=True)

    # Container principal
    main_container = tk.Frame(ventana_resumen, bg="#f5f5f5")
    main_container.pack(fill="both", expand=True, padx=20)

    # Frame izquierdo para pedidos
    left_frame = tk.Frame(main_container, bg="white", relief="solid", bd=1)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

    # Header de pedidos
    pedidos_header = tk.Frame(left_frame, bg="#e3f2fd", height=40)
    pedidos_header.pack(fill="x")
    pedidos_header.pack_propagate(False)
    tk.Label(pedidos_header, text="🛍️ PEDIDOS DEL DÍA", font=("Roboto", 12, "bold"), 
             bg="#e3f2fd", fg="#1976d2").pack(expand=True)

    # Scrollable area para pedidos
    canvas = tk.Canvas(left_frame, bg="white")
    scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
    frame_lista_pedidos = tk.Frame(canvas, bg="white")

    frame_lista_pedidos.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_lista_pedidos, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Frame derecho para estadísticas
    right_frame = tk.Frame(main_container, bg="white", relief="solid", bd=1, width=400)
    right_frame.pack(side="right", fill="y", padx=(10, 0))
    right_frame.pack_propagate(False)

    # Header de estadísticas
    stats_header = tk.Frame(right_frame, bg="#fff3e0", height=40)
    stats_header.pack(fill="x")
    stats_header.pack_propagate(False)
    tk.Label(stats_header, text="📈 ESTADÍSTICAS", font=("Roboto", 12, "bold"), 
             bg="#fff3e0", fg="#e65100").pack(expand=True)

    # Procesar datos
    total_general = 0
    pedidos = []
    refrescos_detalle = {}  # {tipo: cantidad}
    aguas_detalle = {}      # {tipo_tamaño: cantidad}

    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.read().strip().split("===== PEDIDO - ")
        for pedido in contenido[1:]:
            lineas = pedido.strip().split("\n")
            if len(lineas) < 2:
                continue
            fecha_hora = lineas[0].strip()
            fecha = fecha_hora.split()[0]
            domicilio = ""
            total = 0
            items_pedido = []
            
            for linea in lineas:
                if linea.startswith("Domicilio:"):
                    domicilio = linea.replace("Domicilio:", "").strip()
                elif linea.startswith("Total:"):
                    total_str = linea.replace("Total:", "").replace("$", "").strip()
                    try:
                        total = float(total_str)
                        total_general += total
                        pedidos.append((domicilio, fecha, total))
                    except ValueError:
                        continue
                elif linea.startswith("  - "):
                    nombre_item = linea.split("(x")[0].replace("  - ", "").strip()
                    try:
                        cantidad = int(linea.split("(x")[1].split(")")[0]) if "(x" in linea else 1
                        items_pedido.append({"nombre": nombre_item, "cantidad": cantidad})
                    except (IndexError, ValueError):
                        continue
                elif linea.startswith("    Nota:"):
                    if items_pedido:
                        anotacion = linea.replace("    Nota:", "").strip()
                        items_pedido[-1]["anotacion"] = anotacion
            
            # Analizar bebidas específicas por pedido
            for item in items_pedido:
                nombre = item["nombre"]
                cantidad = item["cantidad"]
                anotacion = item.get("anotacion", "") or ""
                
                # Refresco directo
                if nombre == "Refresco":
                    tipo_refresco = anotacion.split(",")[0].strip() if anotacion else "Sin especificar"
                    refrescos_detalle[tipo_refresco] = refrescos_detalle.get(tipo_refresco, 0) + cantidad
                
                # Paquetes con refresco o agua fresca
                elif nombre in ["Paquete 1", "Paquete 2"]:
                    if "agua fresca" in anotacion.lower():
                        # Es agua fresca en paquete
                        if "agua fresca jamaica" in anotacion.lower():
                            aguas_detalle["Jamaica (Paquete)"] = aguas_detalle.get("Jamaica (Paquete)", 0) + cantidad
                        elif "agua fresca horchata" in anotacion.lower():
                            aguas_detalle["Horchata (Paquete)"] = aguas_detalle.get("Horchata (Paquete)", 0) + cantidad
                        else:
                            aguas_detalle["Sin especificar (Paquete)"] = aguas_detalle.get("Sin especificar (Paquete)", 0) + cantidad
                    else:
                        # Es refresco en paquete
                        for tipo in ["COCA", "FANTA", "MANZA", "SPRITE"]:
                            if tipo in anotacion:
                                refrescos_detalle[tipo] = refrescos_detalle.get(tipo, 0) + cantidad
                                break
                        else:
                            # Si no se encontró tipo específico
                            if anotacion and "agua fresca" not in anotacion.lower():
                                tipo_refresco = anotacion.split(",")[0].strip()
                                refrescos_detalle[tipo_refresco] = refrescos_detalle.get(tipo_refresco, 0) + cantidad
                
                # Aguas chicas/grandes
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

    # Mostrar lista de pedidos
    if not pedidos:
        tk.Label(frame_lista_pedidos, text="No hay datos para mostrar", 
                font=("Roboto", 12), bg="white", fg="#666").pack(pady=30)
    else:
        for i, (domicilio, fecha, total) in enumerate(pedidos):
            pedido_frame = tk.Frame(frame_lista_pedidos, bg="#f8f9fa", relief="solid", bd=1)
            pedido_frame.pack(fill="x", padx=15, pady=5)
            
            info_frame = tk.Frame(pedido_frame, bg="#f8f9fa")
            info_frame.pack(fill="x", padx=10, pady=8)
            
            tk.Label(info_frame, text=f"🏠 {domicilio[:25]}{'...' if len(domicilio) > 25 else ''}", 
                    font=("Roboto", 10, "bold"), bg="#f8f9fa", fg="#333").pack(side="left")
            
            middle_frame = tk.Frame(info_frame, bg="#f8f9fa")
            middle_frame.pack(side="left", expand=True)
            tk.Label(middle_frame, text=f"📅 {fecha}", 
                    font=("Roboto", 9), bg="#f8f9fa", fg="#666").pack()
            
            tk.Label(info_frame, text=f"💰 ${int(total)}", 
                    font=("Roboto", 10, "bold"), bg="#f8f9fa", fg="#d32f2f").pack(side="right")
            
            # Botón eliminar
            btn_eliminar = tk.Button(info_frame, text="❌", fg="white", bg="#d32f2f", 
                                   command=lambda idx=i: eliminar_pedido(idx), width=3, 
                                   relief="flat", font=("Roboto", 8))
            btn_eliminar.pack(side="right", padx=(5, 0))
            btn_eliminar.bind("<Enter>", lambda e: btn_eliminar.config(bg="#b71c1c"))
            btn_eliminar.bind("<Leave>", lambda e: btn_eliminar.config(bg="#d32f2f"))

    # Mostrar estadísticas
    stats_content = tk.Frame(right_frame, bg="white")
    stats_content.pack(fill="both", expand=True, padx=15, pady=15)

    # Total general
    total_frame = tk.Frame(stats_content, bg="#e8f5e8", relief="solid", bd=1)
    total_frame.pack(fill="x", pady=(0, 15))
    tk.Label(total_frame, text="💰 TOTAL GENERAL", font=("Roboto", 12, "bold"), 
             bg="#e8f5e8", fg="#2e7d32").pack(pady=5)
    tk.Label(total_frame, text=f"${int(total_general)}", font=("Roboto", 16, "bold"), 
             bg="#e8f5e8", fg="#1b5e20").pack(pady=(0, 10))

    # Refrescos vendidos
    if refrescos_detalle:
        refrescos_frame = tk.Frame(stats_content, bg="#fff3e0", relief="solid", bd=1)
        refrescos_frame.pack(fill="x", pady=(0, 10))
        tk.Label(refrescos_frame, text="🥤 REFRESCOS VENDIDOS", font=("Roboto", 11, "bold"), 
                 bg="#fff3e0", fg="#e65100").pack(pady=5)
        
        for tipo, cantidad in sorted(refrescos_detalle.items()):
            item_frame = tk.Frame(refrescos_frame, bg="#fff3e0")
            item_frame.pack(fill="x", padx=10, pady=1)
            tk.Label(item_frame, text=f"• {tipo}:", font=("Roboto", 9), 
                     bg="#fff3e0", fg="#333").pack(side="left")
            tk.Label(item_frame, text=f"{cantidad}", font=("Roboto", 9, "bold"), 
                     bg="#fff3e0", fg="#d84315").pack(side="right")
        
        tk.Label(refrescos_frame, text="", bg="#fff3e0").pack(pady=2)

    # Aguas frescas vendidas
    if aguas_detalle:
        aguas_frame = tk.Frame(stats_content, bg="#e3f2fd", relief="solid", bd=1)
        aguas_frame.pack(fill="x", pady=(0, 10))
        tk.Label(aguas_frame, text="🧊 AGUAS FRESCAS VENDIDAS", font=("Roboto", 11, "bold"), 
                 bg="#e3f2fd", fg="#1976d2").pack(pady=5)
        
        for tipo, cantidad in sorted(aguas_detalle.items()):
            item_frame = tk.Frame(aguas_frame, bg="#e3f2fd")
            item_frame.pack(fill="x", padx=10, pady=1)
            tk.Label(item_frame, text=f"• {tipo}:", font=("Roboto", 9), 
                     bg="#e3f2fd", fg="#333").pack(side="left")
            tk.Label(item_frame, text=f"{cantidad}", font=("Roboto", 9, "bold"), 
                     bg="#e3f2fd", fg="#0d47a1").pack(side="right")
        
        tk.Label(aguas_frame, text="", bg="#e3f2fd").pack(pady=2)

    # FUNCIÓN PARA IMPRIMIR RESUMEN
    def imprimir_resumen_moderno():
        try:
            printer_name = win32print.GetDefaultPrinter()
            if not printer_name:
                messagebox.showerror("Error", "No se encontró una impresora predeterminada.")
                return

            # Crear resumen para imprimir
            resumen = "=============================\n"
            resumen += "Resumen del Día\n"
            resumen += "=============================\n"
            
            # Mostrar domicilio y total
            for i, (domicilio, fecha, total) in enumerate(pedidos):
                resumen += f"| {domicilio[:20].ljust(20)} | ${int(total)}\n"
            
            resumen += "=============================\n"
            
            if refrescos_detalle:
                resumen += "REFRESCOS VENDIDOS:\n"
                for tipo, cantidad in sorted(refrescos_detalle.items()):
                    resumen += f"  {tipo}: {cantidad}\n"
                resumen += "=============================\n"
            
            if aguas_detalle:
                resumen += "AGUAS FRESCAS VENDIDAS:\n"
                for tipo, cantidad in sorted(aguas_detalle.items()):
                    resumen += f"  {tipo}: {cantidad}\n"
                resumen += "=============================\n"
            
            resumen += f"TOTAL GENERAL: ${int(total_general)}\n"
            resumen += "=============================\n"

            hprinter = win32print.OpenPrinter(printer_name)
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            hdc.StartDoc("Resumen del Día")
            hdc.StartPage()

            font = win32ui.CreateFont({
                "name": "Arial",
                "height": 30,
                "weight": FW_NORMAL
            })
            hdc.SelectObject(font)

            y = 20
            for line in resumen.split('\n'):
                hdc.TextOut(10, y, line.rstrip())
                y += 30

            hdc.EndPage()
            hdc.EndDoc()
            win32print.ClosePrinter(hprinter)
            messagebox.showinfo("Éxito", "Resumen del Día impreso correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo imprimir: {str(e)}")

    # BOTÓN IMPRIMIR RESUMEN
    boton_imprimir = tk.Button(stats_content, text="🖨️ Imprimir Resumen", 
                              font=("Roboto", 11, "bold"), bg="#4caf50", fg="white", 
                              relief="flat", command=imprimir_resumen_moderno)
    boton_imprimir.pack(fill="x", pady=15)
    boton_imprimir.bind("<Enter>", lambda e: boton_imprimir.config(bg="#388e3c"))
    boton_imprimir.bind("<Leave>", lambda e: boton_imprimir.config(bg="#4caf50"))

def convertir_hora_a_minutos(hora_str):
    """Convierte hora en formato AM/PM a minutos desde medianoche para ordenar"""
    try:
        if not hora_str:
            return 9999
            
        hora_str = hora_str.strip().upper()
        
        # Remover espacios entre número y AM/PM y normalizar
        hora_str = hora_str.replace(" AM", "AM").replace(" PM", "PM")
        hora_str = hora_str.replace("A.M.", "AM").replace("P.M.", "PM")
        
        # Determinar si es AM o PM
        es_pm = "PM" in hora_str
        es_am = "AM" in hora_str
        
        # Remover AM/PM para procesar solo la hora
        hora_limpia = hora_str.replace("AM", "").replace("PM", "").strip()
        
        # Si no hay AM/PM, asumir que es PM si está en horario laboral típico
        if not es_am and not es_pm:
            # Para horas entre 7-11, asumir AM. Para 12-5, asumir PM
            hora_temp = int(hora_limpia.split(":")[0]) if ":" in hora_limpia else int(hora_limpia)
            if 7 <= hora_temp <= 11:
                es_am = True
            else:
                es_pm = True
        
        # Separar horas y minutos
        if ":" in hora_limpia:
            partes = hora_limpia.split(":")
            horas = int(partes[0])
            minutos = int(partes[1])
        else:
            horas = int(hora_limpia)
            minutos = 0
        
        # Convertir a formato 24 horas
        if es_am:
            if horas == 12:
                horas = 0  # 12 AM = medianoche (00:00)
        elif es_pm:
            if horas != 12:
                horas += 12  # PM (excepto 12 PM que ya es 12)
        
        # Convertir todo a minutos desde medianoche
        total_minutos = horas * 60 + minutos
        
        return total_minutos
    except Exception as e:
        # Si hay error en el parsing, devolver un valor alto para ponerlo al final
        return 9999

def mostrar_lista_pedidos():
    hoy = date.today().isoformat()
    archivo = f"historial_{hoy}.txt"

    if not os.path.exists(archivo):
        messagebox.showinfo("Sin historial", "No hay pedidos para mostrar hoy.")
        return

    ventana_lista = tk.Toplevel(ventana)
    ventana_lista.title("Lista de pedidos del día")
    window_width = max(int(screen_width * 0.9), 1200)  # Ventana más ancha
    window_height = max(int(screen_height * 0.8), 600)
    ventana_lista.geometry(f"{window_width}x{window_height}")
    ventana_lista.configure(bg="#f5f5f5")
    ventana_lista.minsize(1200, 600)

    # Header principal
    header_frame = tk.Frame(ventana_lista, bg="#2196f3", height=60)
    header_frame.pack(fill="x", pady=(0, 10))
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="📋 Lista de Pedidos del Día", 
             font=("Roboto", 16, "bold"), bg="#2196f3", fg="white").pack(expand=True)

    # Container principal con dos columnas
    main_container = tk.Frame(ventana_lista, bg="#f5f5f5")
    main_container.pack(fill="both", expand=True, padx=20)

    # Frame izquierdo - Sin hora específica
    left_frame = tk.Frame(main_container, bg="white", relief="solid", bd=1)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

    # Header izquierdo
    header_izq = tk.Frame(left_frame, bg="#e8f5e8", height=40)
    header_izq.pack(fill="x")
    header_izq.pack_propagate(False)
    tk.Label(header_izq, text="🕐 PEDIDOS SIN HORA ESPECÍFICA", 
             font=("Roboto", 12, "bold"), bg="#e8f5e8", fg="#2e7d32").pack(expand=True)

    # Scrollable area izquierda
    canvas_izq = tk.Canvas(left_frame, bg="white")
    scrollbar_izq = tk.Scrollbar(left_frame, orient="vertical", command=canvas_izq.yview)
    frame_pedidos_izq = tk.Frame(canvas_izq, bg="white")

    frame_pedidos_izq.bind("<Configure>", lambda e: canvas_izq.configure(scrollregion=canvas_izq.bbox("all")))
    canvas_izq.create_window((0, 0), window=frame_pedidos_izq, anchor="nw")
    canvas_izq.configure(yscrollcommand=scrollbar_izq.set)

    canvas_izq.pack(side="left", fill="both", expand=True)
    scrollbar_izq.pack(side="right", fill="y")

    # Separador visual
    separator = tk.Frame(main_container, bg="#2196f3", width=4)
    separator.pack(side="left", fill="y", padx=5)

    # Frame derecho - Con hora específica
    right_frame = tk.Frame(main_container, bg="white", relief="solid", bd=1)
    right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

    # Header derecho
    header_der = tk.Frame(right_frame, bg="#fff3e0", height=40)
    header_der.pack(fill="x")
    header_der.pack_propagate(False)
    tk.Label(header_der, text="⏰ PEDIDOS CON HORA ESPECÍFICA", 
             font=("Roboto", 12, "bold"), bg="#fff3e0", fg="#e65100").pack(expand=True)

    # Scrollable area derecha
    canvas_der = tk.Canvas(right_frame, bg="white")
    scrollbar_der = tk.Scrollbar(right_frame, orient="vertical", command=canvas_der.yview)
    frame_pedidos_der = tk.Frame(canvas_der, bg="white")

    frame_pedidos_der.bind("<Configure>", lambda e: canvas_der.configure(scrollregion=canvas_der.bbox("all")))
    canvas_der.create_window((0, 0), window=frame_pedidos_der, anchor="nw")
    canvas_der.configure(yscrollcommand=scrollbar_der.set)

    canvas_der.pack(side="left", fill="both", expand=True)
    scrollbar_der.pack(side="right", fill="y")

    # Leer y procesar pedidos
    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.read().strip().split("===== PEDIDO - ")[1:]

    if not contenido:
        tk.Label(frame_pedidos_izq, text="No hay pedidos para mostrar", 
                font=("Roboto", 14), bg="white", fg="#666").pack(pady=50)
        return

    pedidos_sin_hora = []
    pedidos_con_hora = []

    # Separar pedidos con y sin hora específica
    for i, pedido in enumerate(reversed(contenido)):
        lineas = pedido.strip().split("\n")
        if not lineas:
            continue

        # Extraer datos del pedido
        fecha_hora = lineas[0].strip()
        domicilio = ""
        telefono = ""
        cruces = ""
        hora_espec = None
        total = 0
        items = []
        grupo_actual = None
        anotacion_actual = []

        for linea in lineas[1:]:
            if linea.startswith("Domicilio:"):
                domicilio = linea.replace("Domicilio:", "").strip()
            elif linea.startswith("Teléfono:"):
                telefono = linea.replace("Teléfono:", "").strip()
            elif linea.startswith("Cruces:"):
                cruces = linea.replace("Cruces:", "").strip()
            elif linea.startswith("Hora Específica:"):
                hora_espec = linea.replace("Hora Específica:", "").strip()
            elif linea.startswith("Total:"):
                total = float(linea.replace("Total:", "").replace("$", "").strip())
            elif linea.startswith("Cliente:"):
                grupo_actual = linea.replace("Cliente:", "").strip()
            elif linea.startswith("  - "):
                if items and anotacion_actual:
                    items[-1]["anotacion"] = " ".join(anotacion_actual).strip()
                    anotacion_actual = []
                nombre_precio = linea.replace("  - ", "").strip()
                try:
                    if "(x" in nombre_precio:
                        nombre, resto = nombre_precio.split(" (x")
                        cantidad, precio = resto.split(") ($")
                        precio = float(precio.replace(")", ""))
                        cantidad = int(cantidad)
                    else:
                        nombre, precio = nombre_precio.split(" ($")
                        precio = float(precio.replace(")", ""))
                        cantidad = 1
                    items.append({"nombre": nombre, "precio": precio, "anotacion": None, "grupo": grupo_actual, "cantidad": cantidad})
                except ValueError:
                    continue
            elif linea.startswith("    Nota:") or linea.startswith("      "):
                anotacion_actual.append(linea.replace("    Nota: ", "").strip())

        if items and anotacion_actual:
            items[-1]["anotacion"] = " ".join(anotacion_actual).strip()

        pedido_data = {
            "fecha_hora": fecha_hora,
            "domicilio": domicilio,
            "telefono": telefono,
            "cruces": cruces,
            "hora_espec": hora_espec,
            "total": total,
            "items": items
        }

        if hora_espec:
            pedidos_con_hora.append(pedido_data)
        else:
            pedidos_sin_hora.append(pedido_data)

    # Ordenar pedidos con hora específica (de más tarde a más temprano - DESCENDENTE)
    pedidos_con_hora.sort(key=lambda x: convertir_hora_a_minutos(x["hora_espec"]), reverse=True)

    # Función para crear card de pedido - VERSION GRANDE PARA 1280x720
    def crear_card_pedido(pedido_data, frame_padre, mostrar_hora_especifica=False):
        card_frame = tk.Frame(frame_padre, bg="white", relief="solid", bd=2)
        card_frame.pack(fill="x", pady=15, padx=15)

        # Si tiene hora específica, mostrarla primero - MAS GRANDE
        if mostrar_hora_especifica and pedido_data["hora_espec"]:
            hora_frame = tk.Frame(card_frame, bg="#fff3e0")
            hora_frame.pack(fill="x", pady=8)
            tk.Label(hora_frame, text=f"⏰ Hora específica: {pedido_data['hora_espec']}", 
                    font=("Roboto", 14, "bold"), bg="#fff3e0", fg="#e65100").pack(pady=8)

        # Header del card - MAS GRANDE
        card_header = tk.Frame(card_frame, bg="#e3f2fd", height=50)
        card_header.pack(fill="x")
        card_header.pack_propagate(False)

        header_left = tk.Frame(card_header, bg="#e3f2fd")
        header_left.pack(side="left", fill="both", expand=True, padx=20, pady=12)

        # Extraer solo la hora de fecha_hora - FUENTE MAS GRANDE
        solo_hora = pedido_data["fecha_hora"].split(" ")[1] if " " in pedido_data["fecha_hora"] else pedido_data["fecha_hora"]
        tk.Label(header_left, text=f"🕐 {solo_hora}", font=("Roboto", 16, "bold"), 
                bg="#e3f2fd", fg="#1976d2").pack(side="left")

        # Información del cliente - MAS GRANDE Y EXPLICITA
        info_frame = tk.Frame(card_frame, bg="white")
        info_frame.pack(fill="x", padx=20, pady=15)

        # Frame con fondo para datos del cliente
        cliente_frame = tk.Frame(info_frame, bg="#f8f9fa", relief="solid", bd=1)
        cliente_frame.pack(fill="x", pady=5)
        
        tk.Label(cliente_frame, text="📍 INFORMACIÓN DEL CLIENTE", 
                font=("Roboto", 12, "bold"), bg="#f8f9fa", fg="#495057").pack(anchor="w", padx=15, pady=8)

        tk.Label(cliente_frame, text=f"🏠 Dirección: {pedido_data['domicilio']}", font=("Roboto", 11, "bold"), 
                bg="#f8f9fa", fg="#333").pack(anchor="w", padx=20, pady=3)
        tk.Label(cliente_frame, text=f"📞 Teléfono: {pedido_data['telefono']}", font=("Roboto", 11), 
                bg="#f8f9fa", fg="#666").pack(anchor="w", padx=20, pady=2)
        tk.Label(cliente_frame, text=f"🛣️ Cruces: {pedido_data['cruces']}", font=("Roboto", 11), 
                bg="#f8f9fa", fg="#666").pack(anchor="w", padx=20, pady=2)

        # Productos COMPLETAMENTE DESGLOSADOS - MAS GRANDE
        productos_frame = tk.Frame(card_frame, bg="white")
        productos_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(productos_frame, text="🍽️ PRODUCTOS PEDIDOS", font=("Roboto", 12, "bold"), 
                bg="white", fg="#495057").pack(anchor="w", pady=(0, 8))
        
        items_agrupados = {}
        for item in pedido_data["items"]:
            grupo = item.get("grupo", "General")
            items_agrupados.setdefault(grupo, []).append(item)

        for grupo in sorted(items_agrupados.keys(), key=lambda x: (x == "General", x)):
            # Frame del grupo
            grupo_frame = tk.Frame(productos_frame, bg="#fff3e0", relief="solid", bd=1)
            grupo_frame.pack(fill="x", pady=5)
            
            tk.Label(grupo_frame, text=f"👤 Cliente: {grupo.upper()}", 
                    font=("Roboto", 11, "bold"), bg="#fff3e0", fg="#e65100").pack(anchor="w", padx=15, pady=5)
            
            # Desglosar cada producto
            for item in items_agrupados[grupo]:
                item_frame = tk.Frame(grupo_frame, bg="#fff3e0")
                item_frame.pack(fill="x", padx=25, pady=2)
                
                item_text = f"• {item['nombre']} (x{item['cantidad']}) - ${item['precio']:.2f}"
                tk.Label(item_frame, text=item_text, font=("Roboto", 10), 
                        bg="#fff3e0", fg="#333").pack(anchor="w")
                
                # Mostrar anotaciones si las hay - MAS GRANDE Y NOTORIO
                if item['anotacion']:
                    tk.Label(item_frame, text=f"  📝 Nota: {item['anotacion']}", 
                            font=("Roboto", 11, "bold"), bg="#fff3e0", fg="#d84315").pack(anchor="w", pady=2)

        # Footer con precio y botón - MAS GRANDE
        footer_frame = tk.Frame(card_frame, bg="#f8f9fa")
        footer_frame.pack(fill="x", pady=15)
        
        # Precio más grande y prominente
        tk.Label(footer_frame, text=f"💰 Total: ${pedido_data['total']:.2f}", 
                font=("Roboto", 16, "bold"), bg="#f8f9fa", fg="#d32f2f").pack(side="right", padx=20, pady=(0, 8))
        
        ticket = imprimir_ticket_personalizado(pedido_data["fecha_hora"], pedido_data["domicilio"], 
                                             pedido_data["telefono"], pedido_data["cruces"], 
                                             pedido_data["total"], pedido_data["items"])
        
        # Botón más grande
        boton_imprimir = tk.Button(footer_frame, text="🖨️ Imprimir Ticket", 
                                  font=("Roboto", 12, "bold"), bg="#4caf50", fg="white", 
                                  relief="flat", activebackground="#388e3c",
                                  command=lambda t=ticket: imprimir_ticket_directo(t),
                                  padx=20, pady=8)
        boton_imprimir.pack(side="right", padx=20, pady=8)
        boton_imprimir.bind("<Enter>", lambda e: boton_imprimir.config(bg="#388e3c"))
        boton_imprimir.bind("<Leave>", lambda e: boton_imprimir.config(bg="#4caf50"))

    # Mostrar pedidos sin hora específica
    if not pedidos_sin_hora:
        tk.Label(frame_pedidos_izq, text="No hay pedidos sin hora específica", 
                font=("Roboto", 12), bg="white", fg="#666").pack(pady=30)
    else:
        for pedido in pedidos_sin_hora:
            crear_card_pedido(pedido, frame_pedidos_izq, False)

    # Mostrar pedidos con hora específica (ordenados)
    if not pedidos_con_hora:
        tk.Label(frame_pedidos_der, text="No hay pedidos con hora específica", 
                font=("Roboto", 12), bg="white", fg="#666").pack(pady=30)
    else:
        for pedido in pedidos_con_hora:
            crear_card_pedido(pedido, frame_pedidos_der, True)

def limpiar_pedido():
    global ventana_sabores, hora_especifica, grupo_actual, grupos
    pedido_actual.clear()
    for widget in frame_resumen.winfo_children():
        widget.destroy()
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
    actualizar_ticket()

def cambiar_contrasena():
    archivo_clave = "clave.txt"

    if not os.path.exists(archivo_clave):
        with open(archivo_clave, "w") as f:
            f.write("123")

    with open(archivo_clave, "r") as f:
        clave_actual = f.read().strip()

    entrada_actual = simpledialog.askstring("Cambiar contraseña", "Ingresa la contraseña actual:", show="*", parent=ventana)
    if entrada_actual != clave_actual:
        messagebox.showerror("Error", "Contraseña actual incorrecta.")
        return

    nueva_clave = simpledialog.askstring("Nueva contraseña", "Ingresa la nueva contraseña:", show="*", parent=ventana)
    if nueva_clave:
        with open(archivo_clave, "w") as f:
            f.write(nueva_clave)
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

# Inicializar la base de datos al inicio
inicializar_base_datos()

ventana = tk.Tk()
ventana.title("Tortas Ahogadas Doña Susy")
screen_width = ventana.winfo_screenwidth()
screen_height = ventana.winfo_screenheight()
window_width = min(int(screen_width * 0.9), 1152)
window_height = min(int(screen_height * 0.9), 648)
ventana.geometry(f"{window_width}x{window_height}")
ventana.minsize(1000, 600)
ventana.configure(bg="#e6d2a1")
ventana.resizable(True, True)

frame_principal = tk.Frame(ventana, bg="#e6d2a1")
frame_principal.pack(fill="both", expand=True, padx=10, pady=10)
frame_principal.grid_columnconfigure(0, weight=3)  # Más peso al panel izquierdo (botones)
frame_principal.grid_columnconfigure(1, weight=2)  # Menos peso al panel derecho (resumen)
frame_principal.grid_rowconfigure(0, weight=1)

panel_izquierdo = tk.Frame(frame_principal, bg="#ffffff", bd=1, relief="flat")
panel_izquierdo.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

frame_superior_izq = tk.Frame(panel_izquierdo, bg="#ffffff")
frame_superior_izq.pack(fill="both", padx=5, pady=5, expand=True)

tk.Label(
    frame_superior_izq,
    text="Tortas Ahogadas Doña Susy",
    font=("Roboto", 15, "bold"),
    bg="#ffffff",
    fg="#d32f2f",
    pady=5
).pack(anchor="w", fill="x")

frame_datos = tk.Frame(frame_superior_izq, bg="#faf2d3", bd=1, relief="flat")
frame_datos.pack(fill="x", padx=5, pady=5)

# AQUÍ ESTÁ EL CAMBIO: Crear el label con la variable global para poder modificarlo
label_datos_cliente = tk.Label(frame_datos, text="Datos del Cliente", font=("Roboto", 12, "bold"), bg="#faf2d3", fg="#3e2723")
label_datos_cliente.pack(anchor="w", padx=10, pady=5)

for texto, entry_name in [("Domicilio:", "entry_domicilio"), ("Teléfono:", "entry_telefono"), ("Cruces de calle:", "entry_cruces")]:
    frame_entrada = tk.Frame(frame_datos, bg="#faf2d3")
    frame_entrada.pack(fill="x", padx=10, pady=3)
    tk.Label(frame_entrada, text=texto, bg="#faf2d3", font=("Roboto", 10), fg="#3e2723").pack(side="left")
    globals()[entry_name] = tk.Entry(frame_entrada, font=("Roboto", 10), relief="flat", bg="#ffffff", bd=1)
    globals()[entry_name].pack(side="left", padx=5, fill="x", expand=True)
    if entry_name == "entry_telefono":
        entry_telefono.bind("<KeyRelease>", lambda event: buscar_cliente(entry_telefono.get()))

frame_hora = tk.Frame(frame_datos, bg="#faf2d3")
frame_hora.pack(fill="x", padx=10, pady=3)
tk.Label(frame_hora, text="Hora en específico:", bg="#faf2d3", font=("Roboto", 10), fg="#3e2723").pack(side="left")
var_hora = tk.IntVar(value=0)
tk.Radiobutton(frame_hora, text="Sí", variable=var_hora, value=1, bg="#faf2d3", font=("Roboto", 10), fg="#3e2723", command=toggle_hora_entry).pack(side="left", padx=5)
tk.Radiobutton(frame_hora, text="No", variable=var_hora, value=0, bg="#faf2d3", font=("Roboto", 10), fg="#3e2723", command=toggle_hora_entry).pack(side="left", padx=5)
entry_hora = tk.Entry(frame_hora, font=("Roboto", 10), relief="flat", bg="#ffffff", bd=1, state="disabled")
entry_hora.pack(side="left", padx=5, fill="x", expand=True)
def actualizar_hora(event):
    global hora_especifica
    if var_hora.get() == 1:
        hora_especifica = entry_hora.get()
    else:
        hora_especifica = None
entry_hora.bind("<KeyRelease>", actualizar_hora)

tk.Label(frame_superior_izq, text="Selecciona productos:", bg="#ffffff", font=("Roboto", 12, "bold"), fg="#3e2723").pack(pady=5, fill="x")

frame_botones = tk.Frame(frame_superior_izq, bg="#ffffff")
frame_botones.pack(fill="both", expand=True, pady=5)
for i in range(4):
    frame_botones.grid_columnconfigure(i, weight=1, minsize=150)

bebidas = ["Refresco", "Agua Chica", "Agua Grande", "Caguama", "Cerveza"]
comida = ["Torta", "Taco Dorado", "Taco Blandito", "Taco con Carne"]
paquetes = ["Paquete 1", "Paquete 2", "Paquete 3", "Paquete 4", "Paquete 5"]

frame_bebidas = tk.Frame(frame_botones, bg="#ffffff")
frame_bebidas.grid(row=0, column=0, padx=3, sticky="nsew")
tk.Label(frame_bebidas, text="Bebidas", font=("Roboto", 11, "bold"), bg="#ffffff", fg="#d32f2f").pack(pady=2)
for nombre in bebidas:
    btn = tk.Button(frame_bebidas, text=nombre, font=("Roboto", 12), bg="#ff6f00", fg="white", relief="flat",
                    activebackground="#ef6c00", 
                    command=lambda n=nombre: mostrar_ventana_sabores(n) if n in ["Agua Chica", "Agua Grande"] 
                    else mostrar_ventana_refrescos(n) if n == "Refresco" 
                    else agregar_producto(n))
    btn.pack(pady=3, padx=5, fill="x")
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ef6c00"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ff6f00"))

frame_comida = tk.Frame(frame_botones, bg="#ffffff")
frame_comida.grid(row=0, column=1, padx=3, sticky="nsew")
tk.Label(frame_comida, text="Comida", font=("Roboto", 11, "bold"), bg="#ffffff", fg="#d32f2f").pack(pady=2)
for nombre in comida:
    btn = tk.Button(frame_comida, text=nombre, font=("Roboto", 12), bg="#ff6f00", fg="white", relief="flat",
                    activebackground="#ef6c00", command=lambda n=nombre: agregar_producto(n))
    btn.pack(pady=3, padx=5, fill="x")
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ef6c00"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ff6f00"))

btn_carne_gramos = tk.Button(frame_comida, text="Carne(Gramos)", font=("Roboto", 12), bg="#ff6f00", fg="white", relief="flat",
                             activebackground="#ef6c00", command=agregar_carne_gramos)
btn_carne_gramos.pack(pady=3, padx=5, fill="x")
btn_carne_gramos.bind("<Enter>", lambda e: btn_carne_gramos.config(bg="#ef6c00"))
btn_carne_gramos.bind("<Leave>", lambda e: btn_carne_gramos.config(bg="#ff6f00"))

frame_paquetes = tk.Frame(frame_botones, bg="#ffffff")
frame_paquetes.grid(row=0, column=2, padx=3, sticky="nsew")
tk.Label(frame_paquetes, text="Paquetes", font=("Roboto", 11, "bold"), bg="#ffffff", fg="#d32f2f").pack(pady=2)
for nombre in paquetes:
    if nombre in ["Paquete 1", "Paquete 2"]:
        btn = tk.Button(frame_paquetes, text=nombre, font=("Roboto", 12), bg="#ff6f00", fg="white", relief="flat",
                        activebackground="#ef6c00", command=lambda n=nombre: mostrar_ventana_bebida_paquete(n))
    else:
        btn = tk.Button(frame_paquetes, text=nombre, font=("Roboto", 12), bg="#ff6f00", fg="white", relief="flat",
                        activebackground="#ef6c00", command=lambda n=nombre: agregar_producto(n))
    btn.pack(pady=3, padx=5, fill="x")
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ef6c00"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ff6f00"))

frame_nuevo_item = tk.Frame(frame_botones, bg="#ffffff")
frame_nuevo_item.grid(row=0, column=3, padx=3, sticky="nsew")
tk.Label(frame_nuevo_item, text="Otros", font=("Roboto", 11, "bold"), bg="#ffffff", fg="#d32f2f").pack(pady=2)
btn_nuevo_item = tk.Button(frame_nuevo_item, text="Nuevo Ítem", font=("Roboto", 12), bg="#ff6f00", fg="white", relief="flat",
                           activebackground="#ef6c00", command=agregar_nuevo_item)
btn_nuevo_item.pack(pady=3, padx=5, fill="x")
btn_nuevo_item.bind("<Enter>", lambda e: btn_nuevo_item.config(bg="#ef6c00"))
btn_nuevo_item.bind("<Leave>", lambda e: btn_nuevo_item.config(bg="#ff6f00"))

btn_descuento = tk.Button(frame_nuevo_item, text="Descuento", font=("Roboto", 12), bg="#ff6f00", fg="white", relief="flat",
                          activebackground="#ef6c00", command=agregar_descuento)
btn_descuento.pack(pady=3, padx=5, fill="x")
btn_descuento.bind("<Enter>", lambda e: btn_descuento.config(bg="#ef6c00"))
btn_descuento.bind("<Leave>", lambda e: btn_descuento.config(bg="#ff6f00"))

btn_torta_mini = tk.Button(frame_nuevo_item, text="Torta Mini", font=("Roboto", 12), bg="#ff6f00", fg="white", relief="flat",
                           activebackground="#ef6c00", command=lambda: agregar_producto("Torta Mini"))
btn_torta_mini.pack(pady=3, padx=5, fill="x")
btn_torta_mini.bind("<Enter>", lambda e: btn_torta_mini.config(bg="#ef6c00"))
btn_torta_mini.bind("<Leave>", lambda e: btn_torta_mini.config(bg="#ff6f00"))

frame_acciones = tk.Frame(frame_superior_izq, bg="#ffffff")
frame_acciones.pack(fill="x", pady=5)

frame_fila1 = tk.Frame(frame_acciones, bg="#ffffff")
frame_fila1.pack(fill="x", pady=2)

btn_agregar_cliente = tk.Button(frame_fila1, text="Agregar Cliente", command=crear_grupo, bg="#4caf50", fg="white", font=("Roboto", 10), relief="flat")
btn_agregar_cliente.pack(side="left", padx=3, pady=2, fill="x", expand=True)
btn_agregar_cliente.bind("<Enter>", lambda e: btn_agregar_cliente.config(bg="#388e3c"))
btn_agregar_cliente.bind("<Leave>", lambda e: btn_agregar_cliente.config(bg="#4caf50"))

btn_imprimir_ticket = tk.Button(frame_fila1, text="Imprimir Ticket", command=imprimir_ticket, bg="#4caf50", fg="white", font=("Roboto", 10), relief="flat")
btn_imprimir_ticket.pack(side="left", padx=3, pady=2, fill="x", expand=True)
btn_imprimir_ticket.bind("<Enter>", lambda e: btn_imprimir_ticket.config(bg="#388e3c"))
btn_imprimir_ticket.bind("<Leave>", lambda e: btn_imprimir_ticket.config(bg="#4caf50"))

btn_limpiar_pedido = tk.Button(frame_fila1, text="Limpiar Pedido", command=limpiar_pedido, bg="#d32f2f", fg="white", font=("Roboto", 10), relief="flat")
btn_limpiar_pedido.pack(side="left", padx=3, pady=2, fill="x", expand=True)
btn_limpiar_pedido.bind("<Enter>", lambda e: btn_limpiar_pedido.config(bg="#b71c1c"))
btn_limpiar_pedido.bind("<Leave>", lambda e: btn_limpiar_pedido.config(bg="#d32f2f"))

frame_fila2 = tk.Frame(frame_acciones, bg="#ffffff")
frame_fila2.pack(fill="x", pady=2)

btn_resumen = tk.Button(frame_fila2, text="Resumen del Día", command=mostrar_resumen_dia, bg="#0288d1", fg="white", font=("Roboto", 10), relief="flat")
btn_resumen.pack(side="left", padx=3, pady=2, fill="x", expand=True)
btn_resumen.bind("<Enter>", lambda e: btn_resumen.config(bg="#01579b"))
btn_resumen.bind("<Leave>", lambda e: btn_resumen.config(bg="#0288d1"))

btn_lista = tk.Button(frame_fila2, text="Lista de Pedidos", command=mostrar_lista_pedidos, bg="#0288d1", fg="white", font=("Roboto", 10), relief="flat")
btn_lista.pack(side="left", padx=3, pady=2, fill="x", expand=True)
btn_lista.bind("<Enter>", lambda e: btn_lista.config(bg="#01579b"))
btn_lista.bind("<Leave>", lambda e: btn_lista.config(bg="#0288d1"))

frame_footer_izq = tk.Frame(panel_izquierdo, bg="#ffd54f")
frame_footer_izq.pack(side="bottom", fill="x", padx=5, pady=5)

boton_modificar_precio = tk.Button(frame_footer_izq, text="Modificar Precio", command=mostrar_ventana_modificar_precio, bg="#3e2723", fg="white", font=("Roboto", 9), relief="flat")
boton_modificar_precio.pack(side="top", padx=3, pady=2, fill="x")
boton_modificar_precio.bind("<Enter>", lambda e: boton_modificar_precio.config(bg="#2e1b17"))
boton_modificar_precio.bind("<Leave>", lambda e: boton_modificar_precio.config(bg="#3e2723"))

boton_cambiar_clave = tk.Button(frame_footer_izq, text="Cambiar Contraseña", command=cambiar_contrasena, bg="#3e2723", fg="white", font=("Roboto", 9), relief="flat")
boton_cambiar_clave.pack(side="top", padx=3, pady=2, fill="x")
boton_cambiar_clave.bind("<Enter>", lambda e: boton_cambiar_clave.config(bg="#2e1b17"))
boton_cambiar_clave.bind("<Leave>", lambda e: boton_cambiar_clave.config(bg="#3e2723"))

panel_derecho = tk.Frame(frame_principal, bg="#ffffff", bd=1, relief="flat")
panel_derecho.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

tk.Label(panel_derecho, text="Resumen del Pedido:", font=("Roboto", 16, "bold"), bg="#ffffff", fg="#d32f2f").pack(anchor="w", pady=5, fill="x")
frame_resumen = tk.Frame(panel_derecho, bg="#ffffff")
frame_resumen.pack(fill="both", expand=True, anchor="n", padx=5)

# Marca de agua
watermark = tk.Label(ventana, text="Created By BrianP", font=("Roboto", 8), fg="#757575", bg="#e6d2a1")
watermark.place(relx=1.0, rely=1.0, anchor="se", x=-50, y=-20)

# BOTÓN TECLADO TÁCTIL CORREGIDO - Ahora funciona SIEMPRE
btn_teclado = tk.Button(ventana, text="TECLADO", font=("Roboto", 11, "bold"), 
                        bg="#ff5722", fg="white", relief="flat", 
                        activebackground="#d84315", command=abrir_teclado_tactil,
                        width=1, height=1, bd=0, borderwidth=0, 
                        highlightthickness=0, padx=50, pady=50)
btn_teclado.place(relx=1.0, rely=1.0, anchor="se", x=-52, y=-200)
btn_teclado.bind("<Enter>", lambda e: btn_teclado.config(bg="#d84315"))
btn_teclado.bind("<Leave>", lambda e: btn_teclado.config(bg="#ff5722"))

# INICIAR EL CICLO DEL MENSAJE TEMPORAL
iniciar_ciclo_mensaje()

actualizar_ticket()
ventana.mainloop()