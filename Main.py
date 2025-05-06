import tkinter as tk
from tkinter import simpledialog, messagebox
import os
from datetime import datetime, date

# Menú con precios
menu_productos = {
    "Torta": 55,
    "Taco Dorado": 10,
    "Taco Blandito": 25,
    "Refresco": 25,
    "Agua Chica": 15,
    "Agua Grande": 25,
    "Paquete 1": 80,
    "Paquete 2": 85
}

pedido_actual = []
grupos = []
grupo_actual = None

# Centrar texto
def centrar(texto, ancho=32):
    return texto.center(ancho)

def limitar(texto, ancho=32):
    return texto[:ancho]

def agregar_producto(nombre):
    global grupo_actual
    if not any(item["nombre"] == "Envío" for item in pedido_actual):
        pedido_actual.append({
            "nombre": "Envío",
            "anotacion": None,
            "precio": 15,
            "grupo": None
        })

    precio_base = menu_productos[nombre]
    anotacion = simpledialog.askstring("Anotación", f"¿Alguna nota para {nombre}? (Ej. sin verdura)")
    precio_final = precio_base

    if nombre in ["Paquete 1", "Paquete 2"]:
        agregar_agua = messagebox.askyesno("Agua fresca", "¿Agregar agua fresca (+$5)?")
        if agregar_agua:
            precio_final += 5
            anotacion = (anotacion or "") + " (agua fresca)"

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

    frame_contenedor = tk.Frame(frame_resumen, bd=2, relief="groove")
    frame_contenedor.pack(fill="both", expand=True, padx=10, pady=10)

    total = 0
    max_por_columna = 15
    columnas = []
    columna_actual = tk.Frame(frame_contenedor)
    columna_actual.pack(side="left", padx=10, anchor="n")
    columnas.append(columna_actual)

    if not pedido_actual:
        tk.Label(columna_actual, text="(Sin productos aún)", font=("Arial", 10, "italic"), fg="gray").pack(pady=10)
    else:
        items_agrupados = {}
        for item in pedido_actual:
            grupo = item.get("grupo") or "General"
            items_agrupados.setdefault(grupo, []).append(item)

        for grupo, items in items_agrupados.items():
            tk.Label(columna_actual, text=f"Grupo: {grupo}", font=("Arial", 10, "bold"), anchor="w").pack(anchor="w")

            for i, item in enumerate(items):
                if len(columna_actual.winfo_children()) >= max_por_columna:
                    columna_actual = tk.Frame(frame_contenedor)
                    columna_actual.pack(side="left", padx=10, anchor="n")
                    columnas.append(columna_actual)

                texto = f"{item['nombre']} (${item['precio']})"
                if item["anotacion"]:
                    texto += f"\nNota: {item['anotacion']}"

                fila = tk.Frame(columna_actual)
                fila.pack(fill="x", pady=2)

                tk.Label(fila, text=texto, anchor="w", justify="left").pack(side="left")
                idx = pedido_actual.index(item)
                tk.Button(fila, text="X", fg="white", bg="red", command=lambda idx=idx: eliminar_item(idx)).pack(side="right")

                total += item['precio']

    tk.Label(frame_resumen, text=f"\nTOTAL: ${total}", font=("Arial", 12, "bold")).pack(pady=5, anchor="w")

def eliminar_item(indice):
    del pedido_actual[indice]
    actualizar_ticket()

def guardar_en_historial(fecha_hora, domicilio, total):
    hoy = date.today().isoformat()
    with open(f"historial_{hoy}.txt", "a", encoding="utf-8") as f:
        f.write(f"{fecha_hora} | {domicilio} | {total} | {entry_telefono.get()} | {entry_cruces.get()} | {pedido_actual}\n")

def imprimir_ticket_personalizado(fecha, domicilio, telefono, cruces, total, items):
    ticket = f"""
{centrar("TICKET DE PEDIDO")}
{"=" * 32}
Domicilio: {limitar(domicilio)}
Teléfono: {limitar(telefono)}
Cruces: {limitar(cruces)}
Fecha: {fecha}
{"=" * 32}
"""

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
                ticket += f"Nota: {item['anotacion']}\n"

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

    with open("ticket.txt", "w", encoding="utf-8") as f:
        f.write(ticket)

    guardar_en_historial(fecha_hora, domicilio, total)
    os.startfile("ticket.txt", "print")
    messagebox.showinfo("Éxito", "Ticket enviado a imprimir.")

def imprimir_resumen_dia():
    clave = simpledialog.askstring("Contraseña", "Ingresa la contraseña para ver el resumen del día:")
    if clave != "123":
        messagebox.showerror("Acceso denegado", "Contraseña incorrecta.")
        return

    hoy = date.today().isoformat()
    archivo = f"historial_{hoy}.txt"

    if not os.path.exists(archivo):
        messagebox.showinfo("Sin historial", "Aún no hay pedidos registrados.")
        return

    with open(archivo, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    resumen = ""
    total_general = 0

    for linea in lineas:
        partes = linea.strip().split(" | ")
        if len(partes) >= 6:
            fecha, domicilio, total, telefono, cruces, items_str = partes
            try:
                items = eval(items_str)
            except:
                items = []
            total_general += int(total)
            resumen += imprimir_ticket_personalizado(fecha, domicilio, telefono, cruces, total, items)

    resumen += "=" * 32 + "\n"
    resumen += centrar(f"TOTAL GENERAL: ${total_general}") + "\n"
    resumen += "=" * 32 + "\n"

    with open("resumen_dia.txt", "w", encoding="utf-8") as f:
        f.write(resumen)

    os.startfile("resumen_dia.txt", "print")

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

    text_widget = tk.Text(ventana_lista, wrap="word")
    for linea in lineas:
        partes = linea.strip().split(" | ")
        if len(partes) >= 6:
            fecha, domicilio, total, telefono, cruces, items = partes
            text_widget.insert("end", f"Fecha: {fecha}\nDomicilio: {domicilio}\nTeléfono: {telefono}\nCruces: {cruces}\nTotal: ${total}\nItems: {items}\n{'-'*40}\n")

    text_widget.pack(fill="both", expand=True)
    text_widget.config(state="disabled")

def limpiar_pedido():
    pedido_actual.clear()
    for widget in frame_resumen.winfo_children():
        widget.destroy()
    entry_domicilio.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    entry_cruces.delete(0, tk.END)
    actualizar_ticket()

# Interfaz
ventana = tk.Tk()
ventana.title("Tortas Ahogadas Doña Susy")
ventana.geometry("1280x720")

frame_principal = tk.Frame(ventana)
frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

# Panel izquierdo
panel_izquierdo = tk.Frame(frame_principal)
panel_izquierdo.pack(side="left", fill="y", padx=10)

frame_superior_izq = tk.Frame(panel_izquierdo)
frame_superior_izq.pack(fill="x")

# Botón de resumen arriba a la derecha
boton_resumen = tk.Button(frame_principal, text="Resumen del Día", command=imprimir_resumen_dia, bg="blue", fg="white")
boton_resumen.pack(side="top", anchor="ne", pady=5, padx=10)

# Botón de lista de pedidos
boton_lista = tk.Button(frame_principal, text="Lista de Pedidos", command=mostrar_lista_pedidos, bg="purple", fg="white")
boton_lista.pack(side="top", anchor="ne", padx=10)

tk.Label(frame_superior_izq, text="Tortas Ahogadas Doña Susy", font=("Arial", 18, "bold"), anchor="w").pack(anchor="w")

for texto, entry in [("Domicilio:", "entry_domicilio"), ("Teléfono:", "entry_telefono"), ("Cruces de calle:", "entry_cruces")]:
    tk.Label(frame_superior_izq, text=texto).pack(anchor="w")
    globals()[entry] = tk.Entry(frame_superior_izq, width=50)
    globals()[entry].pack()

tk.Label(frame_superior_izq, text="\nSelecciona productos:").pack()
frame_botones = tk.Frame(frame_superior_izq)
frame_botones.pack()

for nombre in menu_productos:
    tk.Button(frame_botones, text=nombre, width=20, command=lambda n=nombre: agregar_producto(n)).pack(pady=2)

tk.Button(frame_superior_izq, text="Nuevo Grupo", command=crear_grupo, bg="orange", fg="white").pack(pady=5)
tk.Button(frame_superior_izq, text="Imprimir ticket", command=imprimir_ticket, bg="green", fg="white").pack(pady=5)
tk.Button(frame_superior_izq, text="Limpiar pedido", command=limpiar_pedido, bg="red", fg="white").pack(pady=2)

# Panel derecho para resumen del pedido
panel_derecho = tk.Frame(frame_principal)
panel_derecho.pack(side="right", fill="both", expand=True)

tk.Label(panel_derecho, text="Resumen del pedido:", font=("Arial", 14, "bold")).pack(anchor="nw")
frame_resumen = tk.Frame(panel_derecho)
frame_resumen.pack(fill="both", expand=True, anchor="n")

actualizar_ticket()
ventana.mainloop()