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
    "Paquete 5": 630
}

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

pedido_actual = []
grupos = []
grupo_actual = None
ventana_sabores = None
hora_especifica = None

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

def limitar(texto, ancho=32):
    return texto[:ancho]

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

def mostrar_ventana_sabores(nombre, callback=None):
    global ventana_sabores
    if ventana_sabores:
        ventana_sabores.destroy()

    ventana_sabores = tk.Toplevel(ventana)
    ventana_sabores.title("Seleccionar Sabor")
    window_width = max(int(screen_width * 0.3), 300)
    window_height = max(int(screen_height * 0.25), 200)
    ventana_sabores.geometry(f"{window_width}x{window_height}")
    ventana_sabores.configure(bg="#faf2d3")
    ventana_sabores.resizable(True, True)
    ventana_sabores.minsize(300, 200)

    tk.Label(ventana_sabores, text=f"Selecciona el sabor para {nombre}", font=("Roboto", 11, "bold"), bg="#faf2d3", fg="#3e2723").pack(pady=10, fill="x")

    frame_btn_sabores = tk.Frame(ventana_sabores, bg="#faf2d3")
    frame_btn_sabores.pack(pady=5, fill="both", expand=True)

    btn_jamaica = tk.Button(frame_btn_sabores, text="Jamaica", font=("Roboto", 10), bg="#4caf50", fg="white", relief="flat",
                            activebackground="#388e3c", command=lambda: [callback("Jamaica") if callback else agregar_producto(nombre, "Jamaica"), ventana_sabores.destroy()])
    btn_jamaica.pack(side="left", padx=10, pady=5, fill="x", expand=True)
    btn_jamaica.bind("<Enter>", lambda e: btn_jamaica.config(bg="#388e3c"))
    btn_jamaica.bind("<Leave>", lambda e: btn_jamaica.config(bg="#4caf50"))

    btn_horchata = tk.Button(frame_btn_sabores, text="Horchata", font=("Roboto", 10), bg="#4caf50", fg="white", relief="flat",
                             activebackground="#388e3c", command=lambda: [callback("Horchata") if callback else agregar_producto(nombre, "Horchata"), ventana_sabores.destroy()])
    btn_horchata.pack(side="left", padx=10, pady=5, fill="x", expand=True)
    btn_horchata.bind("<Enter>", lambda e: btn_horchata.config(bg="#388e3c"))
    btn_horchata.bind("<Leave>", lambda e: btn_horchata.config(bg="#4caf50"))

    ventana_sabores.protocol("WM_DELETE_WINDOW", lambda: ventana_sabores.destroy())

def agregar_kilo_carne():
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
            "grupo": "General"
        })

    gramos = simpledialog.askfloat("Kilo de Carne", "Ingresa la cantidad en gramos:", minvalue=0, parent=ventana)
    if gramos is None:
        return

    precio_kilo = 300
    precio_final = (gramos / 1000) * precio_kilo
    anotacion = simpledialog.askstring("Anotación", "Alguna nota para Kilo de Carne? (Ej. bien cocida)", parent=ventana)

    if gramos is not None:
        item = {
            "nombre": f"Kilo de Carne ({gramos}g)",
            "anotacion": anotacion,
            "precio": round(precio_final, 2),
            "grupo": grupo_actual
        }
        pedido_actual.append(item)
        actualizar_ticket()

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
            "grupo": "General"
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
            "grupo": grupo_actual
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
            "grupo": "General"
        })

    monto = simpledialog.askfloat("Descuento", "Ingresa el monto del descuento:", minvalue=0, parent=ventana)
    if monto is None:
        return

    anotacion = simpledialog.askstring("Nota del Descuento", "Ingresa una nota para el descuento (opcional):", parent=ventana)

    item = {
        "nombre": f"Descuento",
        "anotacion": anotacion,
        "precio": -monto,  # Precio negativo para restar del total
        "grupo": grupo_actual
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
    ventana_precios.configure(bg="#faf2d3")
    ventana_precios.resizable(True, True)
    ventana_precios.minsize(400, 400)

    tk.Label(ventana_precios, text="Modificar Precios del Menú", font=("Roboto", 14, "bold"), bg="#faf2d3", fg="#d32f2f").pack(pady=10, fill="x")

    canvas = tk.Canvas(ventana_precios, bg="#ffffff")
    scrollbar = tk.Scrollbar(ventana_precios, orient="vertical", command=canvas.yview)
    frame_menu = tk.Frame(canvas, bg="#ffffff")

    frame_menu.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_menu, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")

    categorias = {
        "Comida": ["Torta", "Taco Dorado", "Taco Blandito", "Taco con Carne"],
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

def agregar_producto(nombre, sabor_agua=None):
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
            "grupo": "General"
        })

    precio_base = menu_productos[nombre]
    anotacion = sabor_agua

    if nombre not in ["Agua Chica", "Agua Grande"]:
        anotacion = simpledialog.askstring("Anotación", f"¿Alguna nota para {nombre}? (Ej. sin verdura)", parent=ventana)

    precio_final = precio_base

    if nombre in ["Paquete 1", "Paquete 2"]:
        agregar_agua = messagebox.askyesno("Agua fresca", "¿Agregar agua fresca (+$5)?", parent=ventana)
        if agregar_agua:
            precio_final += 5
            grupo_temporal = grupo_actual
            def agregar_sabor(sabor):
                item = {
                    "nombre": nombre,
                    "anotacion": (anotacion or "") + f"(agua fresca {sabor})",
                    "precio": precio_final,
                    "grupo": grupo_temporal
                }
                pedido_actual.append(item)
                actualizar_ticket()
            mostrar_ventana_sabores("Agua Fresca", callback=agregar_sabor)
            return

    item = {
        "nombre": nombre,
        "anotacion": anotacion,
        "precio": precio_final,
        "grupo": grupo_actual or "General"
    }
    pedido_actual.append(item)
    actualizar_ticket()

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

            for item in items_agrupados[grupo]:
                texto = f"{item['nombre']} (${item['precio']:.2f})"
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
    telefono = entry_telefono.get()
    cruces = entry_cruces.get()
    
    items_copy = copy.deepcopy(pedido_actual)
    
    with open(f"historial_{hoy}.txt", "a", encoding="utf-8") as f:
        f.write(f"===== PEDIDO - {fecha_hora} =====\n")
        f.write(f"Fecha y Hora: {fecha_hora}\n")
        f.write(f"Domicilio: {domicilio}\n")
        f.write(f"Teléfono: {telefono}\n")
        f.write(f"Cruces: {cruces}\n")
        if hora_especifica:
            f.write(f"Hora Específica: {hora_especifica}\n")
        f.write("--- Productos ---\n")

        items_agrupados = {}
        for item in items_copy:
            grupo = item.get("grupo", "General")
            items_agrupados.setdefault(grupo, []).append(item)

        for grupo in sorted(items_agrupados.keys(), key=lambda x: (x == "General", x)):
            f.write(f"\nCliente: {grupo.upper()}\n")
            for item in items_agrupados[grupo]:
                f.write(f"  - {item['nombre']} (${item['precio']:.2f})\n")
                if item['anotacion']:
                    f.write(dividir_texto(item['anotacion'], 32, "    Nota: ") + "\n")

        f.write(f"\nTotal: ${total:.2f}\n")
        f.write("=" * 35  + "\n\n")

def imprimir_texto(texto, doc_name="Documento"):
    try:
        printer_name = win32print.GetDefaultPrinter()
        if not printer_name:
            messagebox.showerror("Error", "No se encontró una impresora predeterminada. Configura una en el sistema.")
            return
        
        hprinter = win32print.OpenPrinter(printer_name)
        
        hdc = win32ui.CreateDC()
        try:
            hdc.CreatePrinterDC(printer_name)
        except win32ui.error as e:
            messagebox.showerror("Error", f"No se pudo crear el contexto de dispositivo: {str(e)}")
            win32print.ClosePrinter(hprinter)
            return
        
        hdc.StartDoc(doc_name)
        hdc.StartPage()

        try:
            font = win32ui.CreateFont({
                "name": "Arial",
                "height": 30,
                "weight": FW_NORMAL
            })
            hdc.SelectObject(font)
        except win32ui.error as e:
            messagebox.showerror("Error", f"No se pudo seleccionar la fuente 'Courier New': {str(e)}")
            hdc.EndPage()
            hdc.EndDoc()
            win32print.ClosePrinter(hprinter)
            return

        y = 20
        for line in texto.split('\n'):
            hdc.TextOut(20, y, line.rstrip())
            y += 30

        hdc.EndPage()
        hdc.EndDoc()
        
        win32print.ClosePrinter(hprinter)
        
        messagebox.showinfo("Éxito", f"{doc_name} impreso correctamente.")
    except win32print.error as e:
        messagebox.showerror("Error", f"Error al acceder a la impresora: {str(e)}. Verifica que esté conectada y configurada.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo imprimir: {str(e)}. Contacta al soporte con este mensaje.")

def imprimir_ticket_personalizado(fecha, domicilio, telefono, cruces, total, items):
    global hora_especifica
    ticket = f"""
{centrar("TORTAS AHOGADAS")}
{centrar("DOÑA SUSY")}
{centrar("Geranio #869A")}
{centrar("Col.Tulipanes CP:45647")}
{centrar("33-3684-4525")}
{"=" * 32}
Domicilio: {limitar(domicilio)}
Teléfono: {limitar(telefono)}
Cruces: {limitar(cruces)}
Fecha: {fecha}
"""
    if hora_especifica:
        ticket += f"Hora específica: {hora_especifica}\n"
    ticket += f"{"=" * 32}\n"

    items_agrupados = {}
    for item in items:
        grupo = item.get("grupo", "General")
        items_agrupados.setdefault(grupo, []).append(item)

    for grupo in sorted(items_agrupados.keys(), key=lambda x: (x == "General", x)):
        ticket += "-" * 32 
        ticket += f"\nCliente= {grupo.upper()}\n"
        for item in items_agrupados[grupo]:
            ticket += f"{item['nombre']} (${item['precio']:.2f})\n"
            if item['anotacion']:
                ticket += dividir_texto(item['anotacion']) + "\n"

    ticket += f"{"=" * 32}\n"
    ticket += f"{centrar(f'TOTAL: ${total:.2f}')}\n"
    ticket += f"{centrar('Gracias por su pedido')}\n"
    ticket += f"{"=" * 32}\n"

    return ticket

def imprimir_ticket():
    domicilio = entry_domicilio.get()
    telefono = entry_telefono.get()
    cruces = entry_cruces.get()

    if not domicilio or not telefono or not cruces:
        messagebox.showwarning("Faltan datos", "Debes llenar domicilio, teléfono y cruces.")
        return

    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = sum(item['precio'] for item in pedido_actual)

    items_copy = copy.deepcopy(pedido_actual)

    guardar_actualizar_cliente(telefono, domicilio, cruces)

    guardar_en_historial(fecha_hora, domicilio, total)

    ticket = imprimir_ticket_personalizado(fecha_hora, domicilio, telefono, cruces, total, items_copy)

    imprimir_texto(ticket, "Ticket")

def imprimir_ticket_directo(ticket_texto):
    imprimir_texto(ticket_texto, "Ticket")

def imprimir_ticket_personalizado_2(fecha, domicilio, total, items):
    global hora_especifica
    ticket = f"""
{centrar("TORTAS AHOGADAS DOÑA SUSY")}
{"=" * 32}
Domicilio: {limitar(domicilio)}
Fecha: {fecha}
"""
    if hora_especifica:
        ticket += f"Hora específica: {hora_especifica}\n"
    ticket += f"{"=" * 32}\n"

    items_agrupados = {}
    for item in items:
        grupo = item.get("grupo", "General")
        items_agrupados.setdefault(grupo, []).append(item)

    for grupo in sorted(items_agrupados.keys(), key=lambda x: (x == "General", x)):
        ticket += "-" * 32 + "\n"
        ticket += f"\nCliente= {grupo.upper()}\n"
        for item in items_agrupados[grupo]:
            ticket += f"{item['nombre']} (${item['precio']:.2f})\n"
            if item['anotacion']:
                ticket += dividir_texto(item['anotacion']) + "\n"

    ticket += f"{"=" * 32}\n"
    ticket += f"{centrar(f'TOTAL: ${total:.2f}')}\n"
    ticket += f"{"=" * 32}\n"

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

    resumen = "===== RESUMEN DIA ====\n"
    resumen += "Domicilio   |   Fecha   |  Total\n"
    resumen += "----------- |---------- | ------ \n"

    total_general = 0
    pedidos = []
    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.read().strip().split("===== PEDIDO - ")
        for pedido in contenido[1:]:
            lineas = pedido.strip().split("\n")
            if len(lineas) < 2:
                continue
            fecha_hora = lineas[0].strip()
            fecha = fecha_hora.split()[0]
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

    for domicilio, fecha, total in pedidos:
        resumen += f"{domicilio[:12]} | {fecha} | ${total:.2f}\n"

    if not pedidos:
        messagebox.showinfo("Sin datos", "Sin datos.")
        return

    resumen += "="*32 + "\n"
    resumen += f"TOTAL GENERAL: ${total_general:.2f}\n"
    resumen += "="*32 + "\n"

    ventana_resumen = tk.Toplevel(ventana)
    ventana_resumen.title("Resumen del Día")
    window_width = max(int(screen_width * 0.5), 500)
    window_height = max(int(screen_height * 0.7), 500)
    ventana_resumen.geometry(f"{window_width}x{window_height}")
    ventana_resumen.configure(bg="#faf2d3")
    ventana_resumen.minsize(500, 500)

    canvas = tk.Canvas(ventana_resumen, bg="#ffffff")
    scrollbar = tk.Scrollbar(ventana_resumen, orient="vertical", command=canvas.yview)
    frame_resumen = tk.Frame(canvas, bg="#ffffff")

    frame_resumen.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_resumen, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    marco = tk.Frame(frame_resumen, bd=1, relief="flat", padx=10, pady=10, bg="#ffffff")
    marco.pack(fill="x", padx=15, pady=10)

    tk.Label(marco, text=resumen, justify="left", font=("Courier New", 10), anchor="w", bg="#ffffff", fg="#3e2723").pack(side="left", fill="x", expand=True)

    boton_imprimir = tk.Button(marco, text="Imprimir", bg="#4caf50", fg="white", relief="flat", font=("Roboto", 10), command=lambda: imprimir_texto(resumen, "Resumen del Día"))
    boton_imprimir.pack(side="right", padx=10, pady=10)
    boton_imprimir.bind("<Enter>", lambda e: boton_imprimir.config(bg="#388e3c"))
    boton_imprimir.bind("<Leave>", lambda e: boton_imprimir.config(bg="#4caf50"))

def mostrar_lista_pedidos():
    hoy = date.today().isoformat()
    archivo = f"historial_{hoy}.txt"

    if not os.path.exists(archivo):
        messagebox.showinfo("Sin historial", "No hay pedidos para mostrar hoy.")
        return

    ventana_lista = tk.Toplevel(ventana)
    ventana_lista.title("Lista de pedidos del día")
    window_width = max(int(screen_width * 0.5), 500)
    window_height = max(int(screen_height * 0.7), 500)
    ventana_lista.geometry(f"{window_width}x{window_height}")
    ventana_lista.configure(bg="#faf2d3")
    ventana_lista.minsize(500, 500)

    canvas = tk.Canvas(ventana_lista, bg="#ffffff")
    scrollbar = tk.Scrollbar(ventana_lista, orient="vertical", command=canvas.yview)
    frame_pedidos = tk.Frame(canvas, bg="#ffffff")

    frame_pedidos.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_pedidos, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    with open(archivo, "r", encoding="utf-8") as f:
        contenido = f.read().strip().split("===== PEDIDO - ")[1:]

    for pedido in contenido:
        lineas = pedido.strip().split("\n")
        if not lineas:
            continue

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
                    nombre, precio = nombre_precio.split(" ($")
                    precio = float(precio.replace(")", ""))
                    items.append({"nombre": nombre, "precio": precio, "anotacion": None, "grupo": grupo_actual})
                except ValueError:
                    continue
            elif linea.startswith("    Nota:") or linea.startswith("      "):
                anotacion_actual.append(linea.replace("    Nota: ", "").strip())

        if items and anotacion_actual:
            items[-1]["anotacion"] = " ".join(anotacion_actual).strip()

        ticket = imprimir_ticket_personalizado(fecha_hora, domicilio, telefono, cruces, total, items)

        marco = tk.Frame(frame_pedidos, bd=1, relief="flat", padx=10, pady=10, bg="#ffffff")
        marco.pack(fill="x", padx=15, pady=10)

        tk.Label(marco, text=ticket, justify="left", font=("Courier New", 10), anchor="w", bg="#ffffff", fg="#3e2723").pack(side="left", fill="x", expand=True)

        boton_imprimir = tk.Button(marco, text="Imprimir", bg="#4caf50", fg="white", relief="flat", font=("Roboto", 10), command=lambda t=ticket: imprimir_ticket_directo(t))
        boton_imprimir.pack(side="right", padx=10, pady=10)
        boton_imprimir.bind("<Enter>", lambda e: boton_imprimir.config(bg="#388e3c"))
        boton_imprimir.bind("<Leave>", lambda e: boton_imprimir.config(bg="#4caf50"))

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
    grupo_actual = "General"  # Restablecer grupo_actual a "General"
    grupos = ["General"]      # Reiniciar la lista grupos con solo "General"
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
ventana.configure(bg="#f5e8c7")
ventana.resizable(True, True)

frame_principal = tk.Frame(ventana, bg="#f5e8c7")
frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

# Marca de agua
watermark = tk.Label(frame_principal, text="Created By BrianP", font=("Roboto", 8), fg="#757575", bg="#f5e8c7")
watermark.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

panel_izquierdo = tk.Frame(frame_principal, bg="#ffffff", bd=1, relief="flat")
panel_izquierdo.pack(side="left", fill="y", padx=5, pady=5)

frame_superior_izq = tk.Frame(panel_izquierdo, bg="#ffffff")
frame_superior_izq.pack(fill="both", padx=5, pady=5, expand=True)

tk.Label(
    frame_superior_izq,
    text="Tortas Ahogadas Doña Susy",
    font=("Roboto", 22, "bold"),
    bg="#ffffff",
    fg="#d32f2f",
    pady=5
).pack(anchor="w", fill="x")

frame_datos = tk.Frame(frame_superior_izq, bg="#faf2d3", bd=1, relief="flat")
frame_datos.pack(fill="x", padx=5, pady=5)

tk.Label(frame_datos, text="Datos del Cliente", font=("Roboto", 12, "bold"), bg="#faf2d3", fg="#3e2723").pack(anchor="w", padx=10, pady=5)

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

# Frame para los botones de productos (sin scrollbar)
frame_botones = tk.Frame(frame_superior_izq, bg="#ffffff")
frame_botones.pack(fill="both", expand=True, pady=5)

frame_botones.grid_columnconfigure(0, weight=1)
frame_botones.grid_columnconfigure(1, weight=1)
frame_botones.grid_columnconfigure(2, weight=1)
frame_botones.grid_columnconfigure(3, weight=1)

bebidas = ["Refresco", "Agua Chica", "Agua Grande", "Caguama", "Cerveza"]
comida = ["Torta", "Taco Dorado", "Taco Blandito", "Taco con Carne"]
paquetes = ["Paquete 1", "Paquete 2", "Paquete 3", "Paquete 4", "Paquete 5"]

frame_bebidas = tk.Frame(frame_botones, bg="#ffffff")
frame_bebidas.grid(row=0, column=0, padx=3, sticky="nsew")
tk.Label(frame_bebidas, text="Bebidas", font=("Roboto", 11, "bold"), bg="#ffffff", fg="#d32f2f").pack(pady=2)
for nombre in bebidas:
    btn = tk.Button(frame_bebidas, text=nombre, font=("Roboto", 10), bg="#ff6f00", fg="white", relief="flat",
                    activebackground="#ef6c00", command=lambda n=nombre: mostrar_ventana_sabores(n) if n in ["Agua Chica", "Agua Grande"] else agregar_producto(n))
    btn.pack(pady=1, fill="x", padx=2)
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ef6c00"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ff6f00"))

frame_comida = tk.Frame(frame_botones, bg="#ffffff")
frame_comida.grid(row=0, column=1, padx=3, sticky="nsew")
tk.Label(frame_comida, text="Comida", font=("Roboto", 11, "bold"), bg="#ffffff", fg="#d32f2f").pack(pady=2)
for nombre in comida:
    btn = tk.Button(frame_comida, text=nombre, font=("Roboto", 10), bg="#ff6f00", fg="white", relief="flat",
                    activebackground="#ef6c00", command=lambda n=nombre: agregar_producto(n))
    btn.pack(pady=1, fill="x", padx=2)
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ef6c00"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ff6f00"))

btn_kilo_carne = tk.Button(frame_comida, text="Kilo de Carne", font=("Roboto", 10), bg="#ff6f00", fg="white", relief="flat",
                           activebackground="#ef6c00", command=agregar_kilo_carne)
btn_kilo_carne.pack(pady=1, fill="x", padx=2)
btn_kilo_carne.bind("<Enter>", lambda e: btn_kilo_carne.config(bg="#ef6c00"))
btn_kilo_carne.bind("<Leave>", lambda e: btn_kilo_carne.config(bg="#ff6f00"))

frame_paquetes = tk.Frame(frame_botones, bg="#ffffff")
frame_paquetes.grid(row=0, column=2, padx=3, sticky="nsew")
tk.Label(frame_paquetes, text="Paquetes", font=("Roboto", 11, "bold"), bg="#ffffff", fg="#d32f2f").pack(pady=2)
for nombre in paquetes:
    btn = tk.Button(frame_paquetes, text=nombre, font=("Roboto", 10), bg="#ff6f00", fg="white", relief="flat",
                    activebackground="#ef6c00", command=lambda n=nombre: agregar_producto(n))
    btn.pack(pady=1, fill="x", padx=2)
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ef6c00"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ff6f00"))

frame_nuevo_item = tk.Frame(frame_botones, bg="#ffffff")
frame_nuevo_item.grid(row=0, column=3, padx=3, sticky="nsew")
tk.Label(frame_nuevo_item, text="Otros", font=("Roboto", 11, "bold"), bg="#ffffff", fg="#d32f2f").pack(pady=2)
btn_nuevo_item = tk.Button(frame_nuevo_item, text="Nuevo Ítem", font=("Roboto", 10), bg="#ff6f00", fg="white", relief="flat",
                           activebackground="#ef6c00", command=agregar_nuevo_item)
btn_nuevo_item.pack(pady=1, fill="x", padx=2)
btn_nuevo_item.bind("<Enter>", lambda e: btn_nuevo_item.config(bg="#ef6c00"))
btn_nuevo_item.bind("<Leave>", lambda e: btn_nuevo_item.config(bg="#ff6f00"))

btn_descuento = tk.Button(frame_nuevo_item, text="Descuento", font=("Roboto", 10), bg="#ff6f00", fg="white", relief="flat",
                          activebackground="#ef6c00", command=agregar_descuento)
btn_descuento.pack(pady=1, fill="x", padx=2)
btn_descuento.bind("<Enter>", lambda e: btn_descuento.config(bg="#ef6c00"))
btn_descuento.bind("<Leave>", lambda e: btn_descuento.config(bg="#ff6f00"))

# Frame para botones de acción reorganizados en dos filas
frame_acciones = tk.Frame(frame_superior_izq, bg="#ffffff")
frame_acciones.pack(fill="x", pady=5)

# Primera fila: Agregar Cliente, Imprimir Ticket, Limpiar Pedido
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

# Segunda fila: Resumen del Día, Lista de Pedidos (horizontal)
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

# Nuevo frame para los botones "Modificar Precio" y "Cambiar Contraseña" en el lado izquierdo
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
panel_derecho.pack(side="right", fill="both", expand=True, padx=5, pady=5)

tk.Label(panel_derecho, text="Resumen del Pedido:", font=("Roboto", 16, "bold"), bg="#ffffff", fg="#d32f2f").pack(anchor="nw", pady=5, fill="x")
frame_resumen = tk.Frame(panel_derecho, bg="#ffffff")
frame_resumen.pack(fill="both", expand=True, anchor="n", padx=5)

actualizar_ticket()
ventana.mainloop()