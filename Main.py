import tkinter as tk
from tkinter import simpledialog, messagebox
import os
from datetime import datetime

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

# Formato texto
def centrar(texto, ancho=32):
    return texto.center(ancho)

def limitar(texto, ancho=32):
    return texto[:ancho]

# Agregar producto
def agregar_producto(nombre):
    precio_base = menu_productos[nombre]
    anotacion = simpledialog.askstring("Anotación", f"¿Alguna nota para {nombre}? (Ej. sin verdura)")
    precio_final = precio_base

    if nombre in ["Paquete 1", "Paquete 2"]:
        agregar_agua = messagebox.askyesno("Agua fresca", "¿Agregar agua fresca (+$5)?")
        if agregar_agua:
            precio_final += 5
            anotacion = (anotacion or "") + " (con agua fresca)"

    pedido_actual.append({
        "nombre": nombre,
        "anotacion": anotacion,
        "precio": precio_final
    })

    actualizar_ticket()

# Mostrar pedido en pantalla
def actualizar_ticket():
    texto_ticket.set("")
    total = 0
    for item in pedido_actual:
        linea = f"- {item['nombre']} (${item['precio']})"
        if item["anotacion"]:
            linea += f"\n  Nota: {item['anotacion']}"
        texto_ticket.set(texto_ticket.get() + linea + "\n")
        total += item['precio']
    texto_ticket.set(texto_ticket.get() + f"\nTOTAL: ${total}")

# Guardar pedido en historial
def guardar_en_historial(fecha_hora, domicilio, total):
    with open("historial_dia.txt", "a", encoding="utf-8") as f:
        f.write(f"{fecha_hora} | {domicilio} | {total}\n")

# Imprimir ticket
def imprimir_ticket():
    domicilio = entry_domicilio.get()
    telefono = entry_telefono.get()
    cruces = entry_cruces.get()

    if not domicilio or not telefono or not cruces:
        messagebox.showwarning("Faltan datos", "Debes llenar domicilio, teléfono y cruces.")
        return

    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = sum(item['precio'] for item in pedido_actual)

    ticket = f"""
{centrar("TICKET DE PEDIDO")}
{("=" * 32)}
Domicilio: {limitar(domicilio)}
Teléfono: {limitar(telefono)}
Cruces: {limitar(cruces)}
Fecha: {fecha_hora}
{("=" * 32)}
"""

    for item in pedido_actual:
        ticket += f"{item['nombre']} (${item['precio']})\n"
        if item['anotacion']:
            ticket += f"Nota: {item['anotacion']}\n"

    ticket += f"{('=' * 32)}\n"
    ticket += f"{centrar(f'TOTAL: ${total}')}\n"
    ticket += f"{centrar('Gracias por su pedido')}\n"
    ticket += f"{('=' * 32)}\n"

    with open("ticket.txt", "w", encoding="utf-8") as f:
        f.write(ticket)

    guardar_en_historial(fecha_hora, domicilio, total)
    os.startfile("ticket.txt", "print")
    messagebox.showinfo("Éxito", "Ticket enviado a imprimir.")

# Imprimir resumen del día
def imprimir_resumen_dia():
    if not os.path.exists("historial_dia.txt"):
        messagebox.showinfo("Sin historial", "Aún no hay pedidos registrados.")
        return

    with open("historial_dia.txt", "r", encoding="utf-8") as f:
        lineas = f.readlines()

    resumen = "=" * 32 + "\n"
    resumen += centrar("RESUMEN DE PEDIDOS DEL DÍA") + "\n"
    resumen += "=" * 32 + "\n"

    total_general = 0
    for linea in lineas:
        partes = linea.strip().split(" | ")
        if len(partes) == 3:
            fecha, domicilio, total = partes
            resumen += f"{fecha}\n{domicilio}\nTOTAL: ${total}\n"
            resumen += "-" * 32 + "\n"
            total_general += int(total)

    resumen += "=" * 32 + "\n"
    resumen += centrar(f"TOTAL GENERAL: ${total_general}") + "\n"
    resumen += "=" * 32 + "\n"

    with open("resumen_dia.txt", "w", encoding="utf-8") as f:
        f.write(resumen)

    os.startfile("resumen_dia.txt", "print")

# Limpiar pedido
def limpiar_pedido():
    pedido_actual.clear()
    texto_ticket.set("")
    entry_domicilio.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    entry_cruces.delete(0, tk.END)

# Interfaz
ventana = tk.Tk()
ventana.title("Sistema de Pedidos")
ventana.geometry("500x700")

tk.Label(ventana, text="Domicilio:").pack()
entry_domicilio = tk.Entry(ventana, width=50)
entry_domicilio.pack()

tk.Label(ventana, text="Teléfono:").pack()
entry_telefono = tk.Entry(ventana, width=50)
entry_telefono.pack()

tk.Label(ventana, text="Cruces de calle:").pack()
entry_cruces = tk.Entry(ventana, width=50)
entry_cruces.pack()

tk.Label(ventana, text="\nSelecciona productos:").pack()
frame_botones = tk.Frame(ventana)
frame_botones.pack()

for nombre in menu_productos:
    tk.Button(frame_botones, text=nombre, width=20, command=lambda n=nombre: agregar_producto(n)).pack(pady=2)

texto_ticket = tk.StringVar()
tk.Label(ventana, text="\nResumen del pedido:").pack()
tk.Label(ventana, textvariable=texto_ticket, justify="left").pack()

tk.Button(ventana, text="Imprimir ticket", command=imprimir_ticket, bg="green", fg="white").pack(pady=5)
tk.Button(ventana, text="Limpiar pedido", command=limpiar_pedido).pack(pady=2)
tk.Button(ventana, text="Resumen del Día", command=imprimir_resumen_dia, bg="blue", fg="white").pack(pady=10)

ventana.mainloop()