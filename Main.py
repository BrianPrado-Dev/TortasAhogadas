import tkinter as tk
from tkinter import simpledialog, messagebox
import os
from datetime import datetime, date

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

def imprimir_ticket_directo(ticket_texto):
    with open("ticket_temp.txt", "w", encoding="utf-8") as f:
        f.write(ticket_texto)
    os.startfile("ticket_temp.txt", "print")
def imprimir_ticket_personalizado_2(fecha, domicilio, total, items):
    ticket = f"""
{centrar("TICKET DE PEDIDO")}
{"=" * 32}
Domicilio: {limitar(domicilio)}
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
    ticket += f"{"=" * 32}\n"

    return ticket

def imprimir_resumen_dia():
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
    with open(archivo, "r", encoding="utf-8") as f:
        for linea in f:
            partes = linea.strip().split(" | ")
            if len(partes) >= 6:
                try:
                    fecha, domicilio, total_str, _, _, _ = partes
                    total = int(total_str)
                    total_general += total
                    resumen += f"{domicilio[:12]} | {fecha[:10]} | ${total}\n"
                except (ValueError, SyntaxError):
                    continue

    if not resumen or "Domicilio" not in resumen:
        messagebox.showinfo("Sin datos", "Sin datos.")
        return

    resumen += "="*32 + "\n"
    resumen += f"TOTAL GENERAL: ${total_general}\n"
    resumen += "="*32 + "\n"

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

    canvas = tk.Canvas(ventana_lista)
    scrollbar = tk.Scrollbar(ventana_lista, orient="vertical", command=canvas.yview)
    frame_pedidos = tk.Frame(canvas)

    frame_pedidos.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=frame_pedidos, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    for linea in lineas:
        partes = linea.strip().split(" | ")
        if len(partes) >= 6:
            fecha, domicilio, total, telefono, cruces, items_str = partes
            try:
                items = eval(items_str)
            except:
                items = []

            ticket = imprimir_ticket_personalizado(fecha, domicilio, telefono, cruces, total, items)

            marco = tk.Frame(frame_pedidos, bd=2, relief="groove", padx=5, pady=5)
            marco.pack(fill="x", padx=10, pady=5)

            tk.Label(marco, text=ticket, justify="left", font=("Courier New", 9), anchor="w").pack(side="left", fill="x", expand=True)

            boton_imprimir = tk.Button(marco, text="🖨️", bg="green", fg="white", width=3, height=1, command=lambda t=ticket: imprimir_ticket_directo(t))
            boton_imprimir.pack(side="right", padx=5, pady=5)

def limpiar_pedido():
    pedido_actual.clear()
    for widget in frame_resumen.winfo_children():
        widget.destroy()
    entry_domicilio.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    entry_cruces.delete(0, tk.END)
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

ventana = tk.Tk()
ventana.title("Tortas Ahogadas Doña Susy")
ventana.geometry("1280x720")

frame_principal = tk.Frame(ventana)
frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

panel_izquierdo = tk.Frame(frame_principal)
panel_izquierdo.pack(side="left", fill="y", padx=10)

frame_superior_izq = tk.Frame(panel_izquierdo)
frame_superior_izq.pack(fill="x")

boton_resumen = tk.Button(frame_principal, text="Resumen del Día", command=imprimir_resumen_dia, bg="blue", fg="white")
boton_resumen.pack(side="top", anchor="ne", pady=5, padx=10)

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

tk.Button(frame_superior_izq, text="Agregar Cliente", command=crear_grupo, bg="orange", fg="white").pack(pady=5)
tk.Button(frame_superior_izq, text="Imprimir ticket", command=imprimir_ticket, bg="green", fg="white").pack(pady=5)
tk.Button(frame_superior_izq, text="Limpiar pedido", command=limpiar_pedido, bg="red", fg="white").pack(pady=2)

panel_derecho = tk.Frame(frame_principal)
panel_derecho.pack(side="right", fill="both", expand=True)

tk.Label(panel_derecho, text="Resumen del pedido:", font=("Arial", 14, "bold")).pack(anchor="nw")
frame_resumen = tk.Frame(panel_derecho)
frame_resumen.pack(fill="both", expand=True, anchor="n")

etiqueta_credito = tk.Label(ventana, text="Created by BrianP", font=("Arial", 8), anchor="w")
etiqueta_credito.place(x=10, rely=0.98, anchor="sw")

boton_cambiar_clave = tk.Button(ventana, text="Cambiar contraseña", command=cambiar_contrasena, bg="gray", fg="white")
boton_cambiar_clave.place(relx=0.99, rely=0.98, anchor="se")

actualizar_ticket()
ventana.mainloop()