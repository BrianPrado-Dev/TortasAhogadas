import tkinter as tk
from tkinter import simpledialog, messagebox
import os
from datetime import datetime, date
import win32print
import win32ui
from win32con import *

# Diccionario de productos
menu_productos = {
    "Torta": 55,
    "Taco Dorado": 10,
    "Taco Blandito": 25,
    "Refresco": 25,
    "Agua Chica": 15,
    "Agua Grande": 25,
    "Paquete 1": 80,
    "Paquete 2": 85,
    "Caguama": 70,
    "Cerveza": 25
}

pedido_actual = []
grupos = []
grupo_actual = None
ventana_sabores = None  # Ventana emergente para sabores
hora_especifica = None  # Variable global para almacenar la hora específica

def centrar(texto, ancho=32):
    return texto.center(ancho)

def limitar(texto, ancho=32):
    return texto[:ancho]

def dividir_texto(texto, ancho_max=32, prefijo="Nota: "):
    # Si el texto es None o vacío, no devolver nada
    if not texto:
        return ""
    
    # La primera línea incluye el prefijo "Nota: " (6 caracteres), así que el texto inicial tiene 26 caracteres disponibles
    ancho_primera_linea = ancho_max - len(prefijo)
    lineas = []
    palabras = texto.split()
    linea_actual = []
    longitud_actual = 0

    # Procesar todas las palabras
    for i, palabra in enumerate(palabras):
        # Determinar el ancho máximo dependiendo de si es la primera línea o no
        if not lineas:  # Primera línea
            ancho = ancho_primera_linea
        else:
            ancho = ancho_max

        # Calcular el espacio necesario para la palabra (incluye un espacio si no es la primera palabra en la línea)
        espacio = 1 if linea_actual else 0
        if longitud_actual + len(palabra) + espacio <= ancho:
            linea_actual.append(palabra)
            longitud_actual += len(palabra) + espacio
        else:
            # Si hay palabras acumuladas, añadir la línea actual
            if linea_actual:
                if not lineas:  # Primera línea con prefijo
                    lineas.append(f"{prefijo}{' '.join(linea_actual)}")
                else:  # Líneas siguientes con indentación
                    indentacion = " " * len(prefijo)
                    lineas.append(f"{indentacion}{' '.join(linea_actual)}")
            # Comenzar una nueva línea con la palabra actual
            linea_actual = [palabra]
            longitud_actual = len(palabra)

    # Añadir la última línea si hay palabras restantes
    if linea_actual:
        if not lineas:  # Primera línea con prefijo
            lineas.append(f"{prefijo}{' '.join(linea_actual)}")
        else:  # Líneas siguientes con indentación
            indentacion = " " * len(prefijo)
            lineas.append(f"{indentacion}{' '.join(linea_actual)}")

    return "\n".join(lineas)

def mostrar_ventana_sabores(nombre, callback=None):
    global ventana_sabores
    # Cerrar ventana de sabores si ya existe
    if ventana_sabores:
        ventana_sabores.destroy()

    # Crear ventana emergente
    ventana_sabores = tk.Toplevel(ventana)
    ventana_sabores.title("Seleccionar Sabor")
    ventana_sabores.geometry("250x120")
    ventana_sabores.configure(bg="#f0f0f0")
    ventana_sabores.resizable(False, False)

    # Etiqueta
    tk.Label(ventana_sabores, text=f"Selecciona el sabor para {nombre}", font=("Arial", 10), bg="#f0f0f0").pack(pady=10)

    # Frame para botones
    frame_btn_sabores = tk.Frame(ventana_sabores, bg="#f0f0f0")
    frame_btn_sabores.pack(pady=5)

    # Botones de Jamaica y Horchata
    btn_jamaica = tk.Button(frame_btn_sabores, text="Jamaica", width=10, height=1, font=("Arial", 10), bg="#81c784", fg="white", relief="flat",
                            command=lambda: [callback("Jamaica") if callback else agregar_producto(nombre, "Jamaica"), ventana_sabores.destroy()])
    btn_jamaica.pack(side="left", padx=5)

    btn_horchata = tk.Button(frame_btn_sabores, text="Horchata", width=10, height=1, font=("Arial", 10), bg="#81c784", fg="white", relief="flat",
                             command=lambda: [callback("Horchata") if callback else agregar_producto(nombre, "Horchata"), ventana_sabores.destroy()])
    btn_horchata.pack(side="left", padx=5)

    # Asegurar que la ventana se cierre al cerrar manualmente
    ventana_sabores.protocol("WM_DELETE_WINDOW", lambda: ventana_sabores.destroy())

def agregar_producto(nombre, sabor_agua=None):
    global grupo_actual
    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({
            "nombre": "Envío",
            "anotacion": None,
            "precio": 15,
            "grupo": None
        })

    precio_base = menu_productos[nombre]
    anotacion = sabor_agua  # Usar sabor como anotación si existe

    # Si no es agua, pedir anotación
    if nombre not in ["Agua Chica", "Agua Grande"]:
        anotacion = simpledialog.askstring("Anotación", f"¿Alguna nota para {nombre}? (Ej. sin verdura)")

    precio_final = precio_base

    if nombre in ["Paquete 1", "Paquete 2"]:
        agregar_agua = messagebox.askyesno("Agua fresca", "¿Agregar agua fresca (+$5)?")
        if agregar_agua:
            precio_final += 5
            def agregar_sabor(sabor):
                # Crear el item con la anotación inicial
                item = {
                    "nombre": nombre,
                    "anotacion": (anotacion or "") + f" (agua fresca {sabor})",
                    "precio": precio_final,
                    "grupo": grupo_actual
                }
                pedido_actual.append(item)
                actualizar_ticket()
            mostrar_ventana_sabores("Agua Fresca", callback=agregar_sabor)
            return

    pedido_actual.append({
        "nombre": nombre,
        "anotacion": anotacion,
        "precio": precio_final,
        "grupo": grupo_actual
    })

    actualizar_ticket()

def crear_grupo():
    global grupo_actual
    nombre = simpledialog.askstring("Nuevo grupo", "Nombre del grupo (ej. Ana):")
    if nombre:
        grupo_actual = nombre
        if nombre not in grupos:
            grupos.append(nombre)
        actualizar_ticket()

def actualizar_ticket():
    for widget in frame_resumen.winfo_children():
        widget.destroy()

    frame_contenedor = tk.Frame(frame_resumen, bd=2, relief="groove", bg="#f5f5f5")
    frame_contenedor.pack(fill="both", expand=True, padx=10, pady=10)

    total = 0
    max_por_columna = 15
    columnas = []
    columna_actual = tk.Frame(frame_contenedor, bg="#f5f5f5")
    columna_actual.pack(side="left", padx=10, anchor="n")
    columnas.append(columna_actual)

    if not pedido_actual:
        tk.Label(columna_actual, text="(Sin productos aún)", font=("Arial", 10), fg="gray", bg="#f5f5f5").pack(pady=10)
    else:
        items_agrupados = {}
        for item in pedido_actual:
            grupo = item.get("grupo") or "General"
            items_agrupados.setdefault(grupo, []).append(item)

        for grupo, items in items_agrupados.items():
            tk.Label(columna_actual, text=f"Grupo: {grupo}", font=("Arial", 11, "bold"), anchor="w", bg="#f5f5f5").pack(anchor="w")

            for i, item in enumerate(items):
                if len(columna_actual.winfo_children()) >= max_por_columna:
                    columna_actual = tk.Frame(frame_contenedor, bg="#f5f5f5")
                    columna_actual.pack(side="left", padx=10, anchor="n")
                    columnas.append(columna_actual)

                texto = f"{item['nombre']} (${item['precio']})"
                if item["anotacion"]:
                    texto += f"\n{dividir_texto(item['anotacion'])}"

                fila = tk.Frame(columna_actual, bg="#f5f5f5")
                fila.pack(fill="x", pady=2)

                tk.Label(fila, text=texto, anchor="w", justify="left", bg="#f5f5f5", font=("Arial", 10)).pack(side="left")
                idx = pedido_actual.index(item)
                tk.Button(fila, text="X", fg="white", bg="#e57373", command=lambda idx=idx: eliminar_item(idx), width=3, relief="flat").pack(side="right")

                total += item['precio']

    tk.Label(frame_resumen, text=f"TOTAL: ${total}", font=("Arial", 12, "bold"), bg="#ffecb3", fg="#d32f2f", pady=5, padx=10, relief="groove").pack(pady=10, anchor="w")

def eliminar_item(indice):
    del pedido_actual[indice]
    actualizar_ticket()

def guardar_en_historial(fecha_hora, domicilio, total):
    hoy = date.today().isoformat()
    telefono = entry_telefono.get()
    cruces = entry_cruces.get()
    
    # Formato más legible para el historial
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
        for item in pedido_actual:
            grupo = item.get("grupo") or "General"
            items_agrupados.setdefault(grupo, []).append(item)

        for grupo, items in items_agrupados.items():
            f.write(f"\nCliente: {grupo.upper()}\n")
            for item in items:
                f.write(f"  - {item['nombre']} (${item['precio']})\n")
                if item['anotacion']:
                    f.write(dividir_texto(item['anotacion'], 32, "    Nota: ") + "\n")

        f.write(f"\nTotal: ${total}\n")
        f.write("=" * 35 + "\n\n")

def imprimir_texto(texto, doc_name="Documento"):
    try:
        # Obtener la impresora predeterminada
        printer_name = win32print.GetDefaultPrinter()
        hprinter = win32print.OpenPrinter(printer_name)
        
        # Iniciar trabajo de impresión
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc(doc_name)
        hdc.StartPage()

        # Configurar fuente
        font = win32ui.CreateFont({
            "name": "Courier New",
            "height": 20,
            "weight": FW_NORMAL
        })
        hdc.SelectObject(font)

        # Imprimir líneas del texto
        y = 100
        for line in texto.split('\n'):
            hdc.TextOut(100, y, line.rstrip())
            y += 50

        # Finalizar impresión
        hdc.EndPage()
        hdc.EndDoc()
        win32print.ClosePrinter(hprinter)
        messagebox.showinfo("Éxito", f"{doc_name} impreso correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo imprimir: {str(e)}")

def imprimir_ticket_personalizado(fecha, domicilio, telefono, cruces, total, items):
    global hora_especifica
    ticket = f"""
{centrar("TORTAS AHOGADAS DOÑA SUSY")}
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
        grupo = item.get("grupo") or "General"
        items_agrupados.setdefault(grupo, []).append(item)

    for grupo, items in items_agrupados.items():
        ticket += "-" * 32 + "\n"
        ticket += f"\nCliente= {grupo.upper()}\n"
        for item in items:
            ticket += f"{item['nombre']} (${item['precio']})\n"
            if item['anotacion']:
                ticket += dividir_texto(item['anotacion']) + "\n"

    ticket += f"{"=" * 32}\n"
    ticket += f"{centrar(f'TOTAL: ${total}')}\n"
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

    ticket = imprimir_ticket_personalizado(fecha_hora, domicilio, telefono, cruces, total, pedido_actual)

    # Guardar en historial
    guardar_en_historial(fecha_hora, domicilio, total)

    # Imprimir directamente
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
        grupo = item.get("grupo") or "General"
        items_agrupados.setdefault(grupo, []).append(item)

    for grupo, items in items_agrupados.items():
        ticket += "-" * 32 + "\n"
        ticket += f"\nCliente= {grupo.upper()}\n"
        for item in items:
            ticket += f"{item['nombre']} (${item['precio']})\n"
            if item['anotacion']:
                ticket += dividir_texto(item['anotacion']) + "\n"

    ticket += f"{"=" * 32}\n"
    ticket += f"{centrar(f'TOTAL: ${total}')}\n"
    ticket += f"{"=" * 32}\n"

    return ticket

def mostrar_resumen_dia():
    clave_archivo = "clave.txt"
    if not os.path.exists(clave_archivo):
        with open(clave_archivo, "w") as f:
            f.write("123")
    with open(clave_archivo, "r") as f:
        clave_guardada = f.read().strip()

    clave = simpledialog.askstring("Contraseña", "Contraseña:", show="*")
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
        for pedido in contenido[1:]:  # Ignorar el primer elemento vacío
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
                        total = int(total_str)
                        total_general += total
                        pedidos.append((domicilio, fecha, total))
                    except ValueError:
                        continue

    for domicilio, fecha, total in pedidos:
        resumen += f"{domicilio[:12]} | {fecha} | ${total}\n"

    if not pedidos:
        messagebox.showinfo("Sin datos", "Sin datos.")
        return

    resumen += "="*32 + "\n"
    resumen += f"TOTAL GENERAL: ${total_general}\n"
    resumen += "="*32 + "\n"

    # Mostrar ventana emergente con el resumen
    ventana_resumen = tk.Toplevel(ventana)
    ventana_resumen.title("Resumen del Día")
    ventana_resumen.geometry("600x700")

    canvas = tk.Canvas(ventana_resumen, bg="#f5f5f5")
    scrollbar = tk.Scrollbar(ventana_resumen, orient="vertical", command=canvas.yview)
    frame_resumen = tk.Frame(canvas, bg="#f5f5f5")

    frame_resumen.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_resumen, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    marco = tk.Frame(frame_resumen, bd=2, relief="groove", padx=5, pady=5, bg="#ffffff")
    marco.pack(fill="x", padx=10, pady=5)

    tk.Label(marco, text=resumen, justify="left", font=("Courier New", 9), anchor="w", bg="#ffffff").pack(side="left", fill="x", expand=True)

    boton_imprimir = tk.Button(marco, text="Imprimir", bg="#4caf50", fg="white", width=8, height=1, relief="flat", command=lambda: imprimir_texto(resumen, "Resumen del Día"))
    boton_imprimir.pack(side="right", padx=5, pady=5)

def mostrar_lista_pedidos():
    hoy = date.today().isoformat()
    archivo = f"historial_{hoy}.txt"

    if not os.path.exists(archivo):
        messagebox.showinfo("Sin historial", "No hay pedidos para mostrar hoy.")
        return

    with open(archivo, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    ventana_lista = tk.Toplevel(ventana)
    ventana_lista.title("Lista de pedidos del día")
    ventana_lista.geometry("600x700")

    canvas = tk.Canvas(ventana_lista, bg="#f5f5f5")
    scrollbar = tk.Scrollbar(ventana_lista, orient="vertical", command=canvas.yview)
    frame_pedidos = tk.Frame(canvas, bg="#f5f5f5")

    frame_pedidos.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_pedidos, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    pedido_actual = []
    for linea in lineas:
        if linea.startswith("===== PEDIDO - "):
            if pedido_actual:  # Procesar el pedido anterior
                fecha_hora = pedido_actual[0].replace("===== PEDIDO - ", "").strip()
                domicilio = ""
                total = 0
                telefono = ""
                cruces = ""
                items = []
                anotacion_actual = []
                for l in pedido_actual:
                    if l.startswith("Domicilio:"):
                        domicilio = l.replace("Domicilio:", "").strip()
                    elif l.startswith("Teléfono:"):
                        telefono = l.replace("Teléfono:", "").strip()
                    elif l.startswith("Cruces:"):
                        cruces = l.replace("Cruces:", "").strip()
                    elif l.startswith("Total:"):
                        total = int(l.replace("Total:", "").replace("$", "").strip())
                    elif l.startswith("  - "):
                        if items and anotacion_actual:
                            items[-1]["anotacion"] = " ".join(anotacion_actual).strip()
                            anotacion_actual = []
                        nombre_precio = l.replace("  - ", "").strip()
                        nombre, precio = nombre_precio.split(" ($")
                        precio = int(precio.replace(")", ""))
                        items.append({"nombre": nombre, "precio": precio, "anotacion": None, "grupo": None})
                    elif l.startswith("    Nota:"):
                        anotacion_actual.append(l.replace("    Nota: ", ""))
                    elif l.startswith("      "):  # Líneas continuas de la anotación
                        anotacion_actual.append(l.strip())
                    elif l.startswith("Cliente:"):
                        grupo = l.replace("Cliente:", "").strip()
                        for item in items:
                            item["grupo"] = grupo

                # Asegurarse de asignar la última anotación
                if items and anotacion_actual:
                    items[-1]["anotacion"] = " ".join(anotacion_actual).strip()

                ticket = imprimir_ticket_personalizado(fecha_hora, domicilio, telefono, cruces, total, items)

                marco = tk.Frame(frame_pedidos, bd=2, relief="groove", padx=5, pady=5, bg="#ffffff")
                marco.pack(fill="x", padx=10, pady=5)

                tk.Label(marco, text=ticket, justify="left", font=("Courier New", 9), anchor="w", bg="#ffffff").pack(side="left", fill="x", expand=True)

                boton_imprimir = tk.Button(marco, text="Imprimir", bg="#4caf50", fg="white", width=8, height=1, relief="flat", command=lambda t=ticket: imprimir_ticket_directo(t))
                boton_imprimir.pack(side="right", padx=5, pady=5)

            pedido_actual = [linea]
        else:
            pedido_actual.append(linea)

    # Procesar el último pedido
    if pedido_actual:
        fecha_hora = pedido_actual[0].replace("===== PEDIDO - ", "").strip()
        domicilio = ""
        total = 0
        telefono = ""
        cruces = ""
        items = []
        anotacion_actual = []
        for l in pedido_actual:
            if l.startswith("Domicilio:"):
                domicilio = l.replace("Domicilio:", "").strip()
            elif l.startswith("Teléfono:"):
                telefono = l.replace("Teléfono:", "").strip()
            elif l.startswith("Cruces:"):
                cruces = l.replace("Cruces:", "").strip()
            elif l.startswith("Total:"):
                total = int(l.replace("Total:", "").replace("$", "").strip())
            elif l.startswith("  - "):
                if items and anotacion_actual:
                    items[-1]["anotacion"] = " ".join(anotacion_actual).strip()
                    anotacion_actual = []
                nombre_precio = l.replace("  - ", "").strip()
                nombre, precio = nombre_precio.split(" ($")
                precio = int(precio.replace(")", ""))
                items.append({"nombre": nombre, "precio": precio, "anotacion": None, "grupo": None})
            elif l.startswith("    Nota:"):
                anotacion_actual.append(l.replace("    Nota: ", ""))
            elif l.startswith("      "):  # Líneas continuas de la anotación
                anotacion_actual.append(l.strip())
            elif l.startswith("Cliente:"):
                grupo = l.replace("Cliente:", "").strip()
                for item in items:
                    item["grupo"] = grupo

        # Asegurarse de asignar la última anotación
        if items and anotacion_actual:
            items[-1]["anotacion"] = " ".join(anotacion_actual).strip()

        ticket = imprimir_ticket_personalizado(fecha_hora, domicilio, telefono, cruces, total, items)

        marco = tk.Frame(frame_pedidos, bd=2, relief="groove", padx=5, pady=5, bg="#ffffff")
        marco.pack(fill="x", padx=10, pady=5)

        tk.Label(marco, text=ticket, justify="left", font=("Courier New", 9), anchor="w", bg="#ffffff").pack(side="left", fill="x", expand=True)

        boton_imprimir = tk.Button(marco, text="Imprimir", bg="#4caf50", fg="white", width=8, height=1, relief="flat", command=lambda t=ticket: imprimir_ticket_directo(t))
        boton_imprimir.pack(side="right", padx=5, pady=5)

def limpiar_pedido():
    global ventana_sabores, hora_especifica, grupo_actual
    pedido_actual.clear()
    for widget in frame_resumen.winfo_children():
        widget.destroy()
    entry_domicilio.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    entry_cruces.delete(0, tk.END)
    hora_especifica = None
    var_hora.set(0)  # Restablecer a "No"
    entry_hora.delete(0, tk.END)
    entry_hora.config(state="disabled")
    if ventana_sabores:
        ventana_sabores.destroy()
        ventana_sabores = None
    grupo_actual = "General"  # Reiniciar el cliente a "General"
    actualizar_ticket()

def cambiar_contrasena():
    archivo_clave = "clave.txt"

    if not os.path.exists(archivo_clave):
        with open(archivo_clave, "w") as f:
            f.write("123")

    with open(archivo_clave, "r") as f:
        clave_actual = f.read().strip()

    entrada_actual = simpledialog.askstring("Cambiar contraseña", "Ingresa la contraseña actual:", show="*")
    if entrada_actual != clave_actual:
        messagebox.showerror("Error", "Contraseña actual incorrecta.")
        return

    nueva_clave = simpledialog.askstring("Nueva contraseña", "Ingresa la nueva contraseña:", show="*")
    if nueva_clave:
        with open(archivo_clave, "w") as f:
            f.write(nueva_clave)
        messagebox.showinfo("Éxito", "Contraseña actualizada correctamente.")

def toggle_hora_entry():
    global hora_especifica
    if var_hora.get() == 1:  # Si se selecciona "Sí"
        entry_hora.config(state="normal")
        entry_hora.focus()
    else:  # Si se selecciona "No"
        entry_hora.config(state="disabled")
        entry_hora.delete(0, tk.END)
        hora_especifica = None

# Configuración de la ventana principal
ventana = tk.Tk()
ventana.title("Tortas Ahogadas Doña Susy")
ventana.geometry("1280x720")
ventana.configure(bg="#f0f0f0")  # Fondo gris claro

frame_principal = tk.Frame(ventana, bg="#f0f0f0")
frame_principal.pack(fill="both", expand=True, padx=20, pady=20)

# Panel izquierdo
panel_izquierdo = tk.Frame(frame_principal, bg="#ffffff", bd=2, relief="groove")
panel_izquierdo.pack(side="left", fill="y", padx=10, pady=10)

frame_superior_izq = tk.Frame(panel_izquierdo, bg="#ffffff")
frame_superior_izq.pack(fill="x", padx=10, pady=10)

# Título
tk.Label(
    frame_superior_izq,
    text="Tortas Ahogadas Doña Susy",
    font=("Montserrat", 24, "bold"),
    bg="#ffffff",
    fg="#a52a2a",  # Un tono marrón rojizo más cálido y tradicional
    padx=50,
    pady=10
).pack(anchor="w")

# Frame para los campos de entrada (Domicilio, Teléfono, Cruces, Hora) con fondo resaltado
frame_datos = tk.Frame(frame_superior_izq, bg="#e3e1e1", bd=3, relief="ridge")
frame_datos.pack(fill="x", padx=5, pady=10)

tk.Label(frame_datos, text="Datos del Cliente", font=("Arial", 12, "bold"), bg="#e3e1e1").pack(anchor="w", padx=10, pady=5)

for texto, entry_name in [("Domicilio:", "entry_domicilio"), ("Teléfono:", "entry_telefono"), ("Cruces de calle:", "entry_cruces")]:
    frame_entrada = tk.Frame(frame_datos, bg="#e3e1e1")
    frame_entrada.pack(fill="x", padx=10, pady=5)
    tk.Label(frame_entrada, text=texto, bg="#e3e1e1", font=("Arial", 10)).pack(side="left")
    globals()[entry_name] = tk.Entry(frame_entrada, width=50, font=("Arial", 10), relief="flat", bg="#ffffff")
    globals()[entry_name].pack(side="left", padx=5)

# Apartado Hora en específico
frame_hora = tk.Frame(frame_datos, bg="#e3e1e1")
frame_hora.pack(fill="x", padx=10, pady=5)
tk.Label(frame_hora, text="Hora en específico:", bg="#e3e1e1", font=("Arial", 10)).pack(side="left")
var_hora = tk.IntVar(value=0)  # Por defecto "No"
tk.Radiobutton(frame_hora, text="Sí", variable=var_hora, value=1, bg="#e3e1e1", font=("Arial", 10), command=toggle_hora_entry).pack(side="left", padx=5)
tk.Radiobutton(frame_hora, text="No", variable=var_hora, value=0, bg="#e3e1e1", font=("Arial", 10), command=toggle_hora_entry).pack(side="left", padx=5)
entry_hora = tk.Entry(frame_hora, width=20, font=("Arial", 10), relief="flat", bg="#ffffff", state="disabled")
entry_hora.pack(side="left", padx=5)
def actualizar_hora(event):
    global hora_especifica
    if var_hora.get() == 1:
        hora_especifica = entry_hora.get()
    else:
        hora_especifica = None
entry_hora.bind("<KeyRelease>", actualizar_hora)

# Etiqueta de productos
tk.Label(frame_superior_izq, text="\nSelecciona productos:", bg="#ffffff", font=("Arial", 12, "bold")).pack(pady=5)

# Contenedor para las columnas de productos
frame_botones = tk.Frame(frame_superior_izq, bg="#ffffff")
frame_botones.pack(pady=10)

# Definir productos por categoría
bebidas = ["Refresco", "Agua Chica", "Agua Grande", "Caguama", "Cerveza"]
comida = ["Torta", "Taco Dorado", "Taco Blandito"]
paquetes = ["Paquete 1", "Paquete 2"]

# Columna de Bebidas
frame_bebidas = tk.Frame(frame_botones, bg="#ffffff")
frame_bebidas.pack(side="left", padx=10)
tk.Label(frame_bebidas, text="Bebidas", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=5)
for nombre in bebidas:
    btn = tk.Button(frame_bebidas, text=nombre, width=15, font=("Arial", 10), bg="#ffca28", fg="black", relief="raised",
                    command=lambda n=nombre: mostrar_ventana_sabores(n) if n in ["Agua Chica", "Agua Grande"] else agregar_producto(n))
    btn.pack(pady=2)
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ffb300"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ffca28"))

# Columna de Comida
frame_comida = tk.Frame(frame_botones, bg="#ffffff")
frame_comida.pack(side="left", padx=10)
tk.Label(frame_comida, text="Comida", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=5)
for nombre in comida:
    btn = tk.Button(frame_comida, text=nombre, width=15, font=("Arial", 10), bg="#ffca28", fg="black", relief="raised",
                    command=lambda n=nombre: agregar_producto(n))
    btn.pack(pady=2)
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ffb300"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ffca28"))

# Columna de Paquetes
frame_paquetes = tk.Frame(frame_botones, bg="#ffffff")
frame_paquetes.pack(side="left", padx=10)
tk.Label(frame_paquetes, text="Paquetes", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=5)
for nombre in paquetes:
    btn = tk.Button(frame_paquetes, text=nombre, width=15, font=("Arial", 10), bg="#ffca28", fg="black", relief="raised",
                    command=lambda n=nombre: agregar_producto(n))
    btn.pack(pady=2)
    btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#ffb300"))
    btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#ffca28"))

# Botones de acciones
tk.Button(frame_superior_izq, text="Agregar Cliente", command=crear_grupo, bg="#ff9800", fg="white", font=("Arial", 10), relief="raised", width=20).pack(pady=10)
tk.Button(frame_superior_izq, text="Imprimir Ticket", command=imprimir_ticket, bg="#4caf50", fg="white", font=("Arial", 10), relief="raised", width=20).pack(pady=5)
tk.Button(frame_superior_izq, text="Limpiar Pedido", command=limpiar_pedido, bg="#e57373", fg="white", font=("Arial", 10), relief="raised", width=20).pack(pady=5)

# Panel derecho (resumen)
panel_derecho = tk.Frame(frame_principal, bg="#ffffff", bd=2, relief="groove")
panel_derecho.pack(side="right", fill="both", expand=True, padx=10, pady=10)

tk.Label(panel_derecho, text="Resumen del Pedido:", font=("Arial", 16, "bold"), bg="#ffffff", fg="#d32f2f").pack(anchor="nw", pady=10)
frame_resumen = tk.Frame(panel_derecho, bg="#ffffff")
frame_resumen.pack(fill="both", expand=True, anchor="n", padx=10)

# Botones superiores
boton_resumen = tk.Button(frame_principal, text="Resumen del Día", command=mostrar_resumen_dia, bg="#0288d1", fg="white", font=("Arial", 10), relief="raised", width=15)
boton_resumen.pack(side="top", anchor="ne", pady=5, padx=10)

boton_lista = tk.Button(frame_principal, text="Lista de Pedidos", command=mostrar_lista_pedidos, bg="#7b1fa2", fg="white", font=("Arial", 10), relief="raised", width=15)
boton_lista.pack(side="top", anchor="ne", padx=10)

# Barra inferior
frame_footer = tk.Frame(ventana, bg="#f0f0f0")
frame_footer.pack(side="bottom", fill="x")

etiqueta_credito = tk.Label(frame_footer, text="Created by BrianP", font=("Arial", 8), bg="#f0f0f0", fg="#616161")
etiqueta_credito.pack(side="left", padx=10, pady=5)

boton_cambiar_clave = tk.Button(frame_footer, text="Cambiar Contraseña", command=cambiar_contrasena, bg="#616161", fg="white", font=("Arial", 8), relief="raised")
boton_cambiar_clave.pack(side="right", padx=10, pady=5)

actualizar_ticket()
ventana.mainloop()