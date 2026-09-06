import flet as ft
import json
import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fpdf import FPDF

try:
    from flet_android_notifications import FletAndroidNotifications
    ANDROID_NOTIF_DISPONIBLE = True
except ImportError:
    ANDROID_NOTIF_DISPONIBLE = False

DB_FILE = "usuarios_data.json"

DIAS_ES = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}
MESES_ES = {
    "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
    "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
    "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
}

def obtener_fecha_es():
    ahora = datetime.now(ZoneInfo("America/Bogota"))
    return f"{DIAS_ES.get(ahora.strftime('%A'), '')} {ahora.day} de {MESES_ES.get(ahora.strftime('%B'), '')} de {ahora.year}"

def cargar_datos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "admin": {
            "password": "admin",
            "telefono": "3000000000",
            "transacciones": [],
            "metas": [],
            "checklist": {
                "config": {
                    "mañana": "Revisa tus gastos hormiga de la mañana",
                    "hora_mañana": "08:00 AM",
                    "tarde": "Registra tus movimientos de la tarde",
                    "hora_tarde": "02:00 PM",
                    "noche": "Evalúa tu meta de ahorro nocturna",
                    "hora_noche": "08:00 PM"
                },
                "dias": {},
                "metas_periodo": {"diaria": 10000.0, "semanal": 50000.0, "mensual": 200000.0}
            }
        },
        "sesion_activa": None
    }

def guardar_datos(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def formato_cop(valor):
    if valor < 0:
        return f"-${abs(valor):,.0f}".replace(",", ".")
    return f"${valor:,.0f}".replace(",", ".")

def parsear_monto(texto):
    if not texto:
        return 0.0
    limpio = re.sub(r"[^\d]", "", str(texto))
    return float(limpio) if limpio else 0.0

def recalcular_metas(usuario_data):
    for meta in usuario_data.get("metas", []):
        nombre = meta["Meta"]
        acumulado = 0.0
        for t in usuario_data.get("transacciones", []):
            if t.get("Meta_Asociada") == nombre:
                monto = t.get("Monto", 0.0)
                tipo = t.get("Tipo")
                cat = t.get("Categoría")
                if tipo == "Ahorro / Inversión" or cat == "Ahorro Meta":
                    acumulado += monto
                elif cat == "Uso Fondo Meta":
                    acumulado -= monto
        meta["Actual"] = max(0.0, acumulado)

def agregar_cabecera_pdf(pdf, titulo):
    logo_path = "logo-bytepulse.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=10, w=24)
    
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(13, 148, 136)
    pdf.cell(0, 8, "BYTEPULSE", 0, 1, "R")
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, titulo, 0, 1, "R")
    pdf.ln(5)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

def generar_pdf_bytepulse(usuario, datos_user):
    pdf = FPDF()
    pdf.add_page()
    agregar_cabecera_pdf(pdf, "REPORTE FINANCIERO")
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 6, f"Usuario: {usuario} | Fecha de emisión: {obtener_fecha_es()}", 0, 1, "L")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "Historial de Movimientos:", 0, 1)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(31, 41, 55)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(22, 8, "Fecha", 1, 0, "C", True)
    pdf.cell(25, 8, "Tipo", 1, 0, "C", True)
    pdf.cell(35, 8, "Categoria", 1, 0, "C", True)
    pdf.cell(30, 8, "Monto", 1, 0, "C", True)
    pdf.cell(45, 8, "Meta Asociada", 1, 1, "C", True)

    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    for t in datos_user.get("transacciones", []):
        pdf.cell(22, 7, str(t.get("Fecha", "")), 1, 0, "C")
        pdf.cell(25, 7, str(t.get("Tipo", "")), 1, 0, "C")
        pdf.cell(35, 7, str(t.get("Categoría", "")), 1, 0, "C")
        pdf.cell(30, 7, formato_cop(t.get("Monto", 0)), 1, 0, "R")
        pdf.cell(45, 7, str(t.get("Meta_Asociada", "Ninguna")), 1, 1, "L")

    filename = f"reporte_bytepulse_{usuario}.pdf"
    pdf.output(filename)
    return filename

def generar_pdf_checklist(usuario, datos_user):
    pdf = FPDF()
    pdf.add_page()
    agregar_cabecera_pdf(pdf, "REPORTE CHECKLIST Y AHORROS")
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 6, f"Usuario: {usuario} | Fecha de emisión: {obtener_fecha_es()}", 0, 1, "L")
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "Historial Diario de Ahorros:", 0, 1)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(31, 41, 55)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(35, 8, "Fecha", 1, 0, "C", True)
    pdf.cell(40, 8, "Monto Día", 1, 0, "C", True)
    pdf.cell(45, 8, "Acumulado", 1, 1, "C", True)

    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    checklist_data = datos_user.get("checklist", {}).get("dias", {})
    acumulado = 0.0
    for fecha, info in sorted(checklist_data.items()):
        monto_dia = info.get("monto_dia", 0.0)
        acumulado += monto_dia
        pdf.cell(35, 7, str(fecha), 1, 0, "C")
        pdf.cell(40, 7, formato_cop(monto_dia), 1, 0, "R")
        pdf.cell(45, 7, formato_cop(acumulado), 1, 1, "R")

    filename = f"reporte_checklist_{usuario}.pdf"
    pdf.output(filename)
    return filename

def obtener_imagen_segura(ruta, ancho, alto, radio=0):
    if os.path.exists(os.path.join("assets", ruta)) or os.path.exists(ruta):
        return ft.Image(src=ruta, width=ancho, height=alto, border_radius=radio, fit="cover")
    else:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ELECTRIC_BOLT, color="cyan", size=30),
                ft.Text("Bytepulse", size=9, color="cyan", weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=0),
            width=ancho, height=alto,
            bgcolor="#1f2937",
            border_radius=radio,
            alignment="center"
        )

def main(page: ft.Page):
    page.title = "Bytepulse"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 412
    page.window.height = 870
    page.padding = 0

    db = cargar_datos()
    usuario_actual = {"nombre": None}
    
    notifications = FletAndroidNotifications() if ANDROID_NOTIF_DISPONIBLE else None

    def mostrar_alerta(mensaje):
        snack = ft.SnackBar(ft.Text(mensaje))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    logo_widget = ft.Container(
        content=ft.Row([
            obtener_imagen_segura("logo-bytepulse.png", 45, 45, 22.5),
            ft.Column([
                ft.Text("BYTEPULSE", weight=ft.FontWeight.BOLD, size=16, color="cyan"),
                ft.Text("by Quantumsoft", size=10, color="grey")
            ], spacing=0)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
        bgcolor="#111827",
        padding=12,
        border_radius=12
    )

    def mostrar_login():
        page.clean()
        user_input = ft.TextField(label="Usuario", width=280)
        pass_input = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=280)

        def intentar_login(e):
            u = user_input.value.strip()
            p = pass_input.value.strip()
            if u in db and u != "sesion_activa" and db[u].get("password") == p:
                usuario_actual["nombre"] = u
                db["sesion_activa"] = u
                guardar_datos(db)
                mostrar_dashboard_principal()
            else:
                mostrar_alerta("Usuario o contraseña incorrectos")

        def mostrar_recuperacion(e):
            page.clean()
            rec_user_input = ft.TextField(label="Usuario", width=280)
            rec_tel_input = ft.TextField(label="Teléfono registrado", prefix_icon="phone", width=280)
            
            def procesar_recuperacion(e):
                u = rec_user_input.value.strip()
                tel = rec_tel_input.value.strip()
                if u in db and db[u].get("telefono") == tel:
                    mostrar_alerta(f"Tu contraseña es: {db[u].get('password')}")
                    mostrar_login()
                else:
                    mostrar_alerta("Usuario o teléfono incorrectos")

            page.add(
                ft.Container(
                    content=ft.Column([
                        obtener_imagen_segura("logo-bytepulse.png", 100, 100, 50),
                        logo_widget,
                        ft.Text("🔄 Recuperar Contraseña", size=16, weight=ft.FontWeight.BOLD),
                        rec_user_input, rec_tel_input,
                        ft.FilledButton("Recuperar", on_click=procesar_recuperacion, width=280),
                        ft.TextButton("⬅️ Volver al Login", on_click=lambda e: mostrar_login())
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor="#111827", padding=20, border_radius=12, expand=True
                )
            )
            page.update()

        page.add(
            ft.Container(
                content=ft.Column([
                    obtener_imagen_segura("logo-bytepulse.png", 120, 120, 60),
                    ft.Container(height=10),
                    logo_widget,
                    ft.Text(obtener_fecha_es(), size=11, color="grey"),
                    ft.Container(height=15),
                    ft.Text("🔑 Iniciar Sesión", size=16, weight=ft.FontWeight.BOLD),
                    user_input, pass_input,
                    ft.FilledButton("Entrar", on_click=intentar_login, width=280),
                    ft.TextButton("🔑 ¿Olvidaste tu contraseña?", on_click=mostrar_recuperacion),
                    ft.TextButton("📝 ¿No tienes cuenta? Regístrate aquí", on_click=lambda e: mostrar_registro())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="#111827", padding=20, border_radius=12, expand=True
            )
        )
        page.update()

    def mostrar_registro():
        page.clean()
        user_reg_input = ft.TextField(label="Nuevo Usuario", width=280)
        pass_reg_input = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, width=280)
        tel_reg_input = ft.TextField(label="Número Telefónico (Recuperación)", prefix_icon="phone", keyboard_type=ft.KeyboardType.PHONE, width=280)

        def intentar_registro(e):
            u = user_reg_input.value.strip()
            p = pass_reg_input.value.strip()
            tel = tel_reg_input.value.strip()

            if not u or not p or not tel:
                mostrar_alerta("Todos los campos son obligatorios")
                return
            if u in db:
                mostrar_alerta("El usuario ya existe")
                return

            db[u] = {
                "password": p,
                "telefono": tel,
                "transacciones": [],
                "metas": [],
                "checklist": {
                    "config": {
                        "mañana": "Revisa tus gastos hormiga de la mañana", "hora_mañana": "08:00 AM",
                        "tarde": "Registra tus movimientos de la tarde", "hora_tarde": "02:00 PM",
                        "noche": "Evalúa tu meta de ahorro nocturna", "hora_noche": "08:00 PM"
                    },
                    "dias": {},
                    "metas_periodo": {"diaria": 10000.0, "semanal": 50000.0, "mensual": 200000.0}
                }
            }
            db["sesion_activa"] = u
            guardar_datos(db)
            usuario_actual["nombre"] = u
            mostrar_alerta("¡Cuenta creada con éxito!")
            mostrar_dashboard_principal()

        page.add(
            ft.Container(
                content=ft.Column([
                    obtener_imagen_segura("logo-bytepulse.png", 100, 100, 50),
                    logo_widget,
                    ft.Text("✍️ Crear Nueva Cuenta", size=16, weight=ft.FontWeight.BOLD),
                    user_reg_input, pass_reg_input, tel_reg_input,
                    ft.FilledButton("Registrarse", on_click=intentar_registro, width=280),
                    ft.TextButton("⬅️ Volver al Login", on_click=lambda e: mostrar_login())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="#111827", padding=20, border_radius=12, expand=True
            )
        )
        page.update()

    def mostrar_dashboard_principal():
        page.clean()
        uname = usuario_actual["nombre"]
        datos_user = db[uname]
        
        if "checklist" not in datos_user:
            datos_user["checklist"] = {
                "config": {
                    "mañana": "Revisa tus gastos hormiga de la mañana", "hora_mañana": "08:00 AM",
                    "tarde": "Registra tus movimientos de la tarde", "hora_tarde": "02:00 PM",
                    "noche": "Evalúa tu meta de ahorro nocturna", "hora_noche": "08:00 PM"
                },
                "dias": {},
                "metas_periodo": {"diaria": 10000.0, "semanal": 50000.0, "mensual": 200000.0}
            }

        area_contenido = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=15)
        
        sidebar = ft.Container(
            content=ft.Column([
                ft.Row([
                    obtener_imagen_segura("logo-bytepulse.png", 35, 35, 17.5),
                    ft.Text("Menú Bytepulse", weight=ft.FontWeight.BOLD, color="white", size=14)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Row([ft.Icon(ft.Icons.PERSON, size=14, color="cyan"), ft.Text(uname, weight=ft.FontWeight.BOLD, color="white", size=12)], spacing=5),
                ft.Text(obtener_fecha_es(), size=9, color="grey"),
                ft.Divider(),
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            width=250,
            bgcolor="#181d24",
            padding=15,
            visible=False,
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
        )

        def toggle_menu(e):
            sidebar.visible = not sidebar.visible
            page.update()

        def cerrar_sesion_app(e):
            db["sesion_activa"] = None
            guardar_datos(db)
            usuario_actual["nombre"] = None
            mostrar_login()

        def actualizar_contenido(seccion):
            sidebar.visible = False
            area_contenido.controls.clear()
            recalcular_metas(datos_user)
            df = datos_user["transacciones"]

            if seccion == "Dashboard":
                ingresos = sum(t["Monto"] for t in df if t["Tipo"] == "Ingreso")
                gastos = sum(t["Monto"] for t in df if t["Tipo"] == "Gasto" and t["Categoría"] != "Uso Fondo Meta")
                ahorros = sum(t["Monto"] for t in df if t["Tipo"] == "Ahorro / Inversión")

                area_contenido.controls.extend([
                    logo_widget,
                    ft.Text("📊 Dashboard Financiero", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(obtener_fecha_es(), size=11, color="grey"),
                    ft.Column([
                        ft.Container(content=ft.Column([ft.Text("Ingresos", size=11, color="grey"), ft.Text(formato_cop(ingresos), size=15, weight=ft.FontWeight.BOLD)]), padding=12, bgcolor="#1f2937", border_radius=8),
                        ft.Container(content=ft.Column([ft.Text("Gastos", size=11, color="grey"), ft.Text(formato_cop(gastos), size=15, weight=ft.FontWeight.BOLD)]), padding=12, bgcolor="#1f2937", border_radius=8),
                        ft.Container(content=ft.Column([ft.Text("Ahorros", size=11, color="grey"), ft.Text(formato_cop(ahorros), size=15, weight=ft.FontWeight.BOLD)]), padding=12, bgcolor="#1f2937", border_radius=8),
                    ], spacing=8),
                    ft.Divider(),
                    ft.Text("🍩 Tipos de Movimiento", size=16, weight=ft.FontWeight.BOLD)
                ])

                tipos_conteo = {}
                for t in df:
                    tp = t.get("Tipo", "Gasto")
                    tipos_conteo[tp] = tipos_conteo.get(tp, 0) + t.get("Monto", 0)

                total_monto_all = sum(tipos_conteo.values()) if tipos_conteo else 1
                for tp, val in tipos_conteo.items():
                    porcentaje = (val / total_monto_all) * 100
                    area_contenido.controls.append(
                        ft.Column([
                            ft.Row([ft.Text(tp, size=13, weight=ft.FontWeight.BOLD), ft.Text(f"{formato_cop(val)} ({porcentaje:.1f}%)", size=12)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.ProgressBar(value=porcentaje/100, width=350, color="cyan", bgcolor="#374151")
                        ], spacing=3)
                    )

            elif seccion == "Movimientos":
                tipo_input = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Gasto"), ft.dropdown.Option("Ingreso"), ft.dropdown.Option("Deuda"), ft.dropdown.Option("Ahorro / Inversión")], value="Gasto")
                monto_input = ft.TextField(label="Monto (COP $)")
                cat_input = ft.Dropdown(label="Categoría", options=[ft.dropdown.Option("Nómina"), ft.dropdown.Option("Alimentación"), ft.dropdown.Option("Servicios"), ft.dropdown.Option("Transporte"), ft.dropdown.Option("Ahorro Meta"), ft.dropdown.Option("Uso Fondo Meta"), ft.dropdown.Option("Otros")], value="Alimentación")
                desc_input = ft.TextField(label="Descripción")
                meta_asoc_input = ft.Dropdown(label="Meta Asociada", options=[ft.dropdown.Option("Ninguna")] + [ft.dropdown.Option(m["Meta"]) for m in datos_user.get("metas", [])], value="Ninguna")

                def guardar_mov(e):
                    m = parsear_monto(monto_input.value)
                    if m > 0:
                        datos_user["transacciones"].append({
                            "Fecha": datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d"),
                            "Tipo": tipo_input.value, "Categoría": cat_input.value,
                            "Monto": m, "Descripción": desc_input.value or "",
                            "Meta_Asociada": meta_asoc_input.value or "Ninguna"
                        })
                        recalcular_metas(datos_user)
                        guardar_datos(db)
                        actualizar_contenido("Movimientos")
                        mostrar_alerta("¡Movimiento guardado con éxito!")
                    else:
                        mostrar_alerta("Ingrese un monto válido.")

                def eliminar_movimiento(i_row):
                    if 0 <= i_row < len(datos_user["transacciones"]):
                        datos_user["transacciones"].pop(i_row)
                        recalcular_metas(datos_user)
                        guardar_datos(db)
                        actualizar_contenido("Movimientos")
                        mostrar_alerta("Movimiento eliminado correctamente")

                filas_movs_generales = []
                filas_ahorros = []

                for idx, t in enumerate(datos_user["transacciones"]):
                    tipo = t.get("Tipo", "")
                    def crear_eliminar_fn(i_r):
                        return lambda e: eliminar_movimiento(i_r)

                    celdas = [
                        ft.DataCell(ft.Text(t.get("Fecha", ""))),
                        ft.DataCell(ft.Text(tipo)),
                        ft.DataCell(ft.Text(t.get("Categoría", ""))),
                        ft.DataCell(ft.Text(formato_cop(t.get("Monto", 0)))),
                        ft.DataCell(ft.Text(t.get("Meta_Asociada", "Ninguna"))),
                        ft.DataCell(ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=crear_eliminar_fn(idx)))
                    ]

                    if tipo == "Ahorro / Inversión":
                        filas_ahorros.append(ft.DataRow(cells=celdas))
                    else:
                        filas_movs_generales.append(ft.DataRow(cells=celdas))

                tabla_generales = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Fecha")), ft.DataColumn(ft.Text("Tipo")),
                        ft.DataColumn(ft.Text("Cat.")), ft.DataColumn(ft.Text("Monto")),
                        ft.DataColumn(ft.Text("Meta")), ft.DataColumn(ft.Text("Acción")),
                    ],
                    rows=filas_movs_generales
                )

                tabla_ahorros = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Fecha")), ft.DataColumn(ft.Text("Tipo")),
                        ft.DataColumn(ft.Text("Cat.")), ft.DataColumn(ft.Text("Monto")),
                        ft.DataColumn(ft.Text("Meta")), ft.DataColumn(ft.Text("Acción")),
                    ],
                    rows=filas_ahorros
                )

                def exportar_pdf(e):
                    try:
                        fname = generar_pdf_bytepulse(uname, datos_user)
                        mostrar_alerta(f"¡PDF generado: {fname}!")
                    except Exception as ex:
                        mostrar_alerta(f"Error al generar PDF: {ex}")

                area_contenido.controls.extend([
                    logo_widget,
                    ft.Text("📝 Registrar Movimiento", size=18, weight=ft.FontWeight.BOLD),
                    tipo_input, monto_input, cat_input, desc_input, meta_asoc_input,
                    ft.FilledButton("Guardar Transacción", on_click=guardar_mov),
                    ft.Divider(),
                    ft.Row([
                        ft.Text("📋 Mov. Generales", size=16, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.PICTURE_AS_PDF, icon_color="cyan", on_click=exportar_pdf, tooltip="Descargar PDF")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([tabla_generales], scroll=ft.ScrollMode.AUTO),
                    ft.Divider(),
                    ft.Text("💰 Ahorros e Inversiones", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([tabla_ahorros], scroll=ft.ScrollMode.AUTO)
                ])

            elif seccion == "Ahorro":
                meta_nombre = ft.TextField(label="Nombre de la Meta")
                meta_obj = ft.TextField(label="Monto Objetivo (COP $)")
                f_inicio_input = ft.TextField(label="Fecha Inicio (YYYY-MM-DD)", value=datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d"))
                f_fin_input = ft.TextField(label="Fecha Fin (YYYY-MM-DD)", value="2026-12-31")

                def crear_meta(e):
                    mo = parsear_monto(meta_obj.value)
                    if meta_nombre.value and mo > 0:
                        datos_user["metas"].append({
                            "Meta": meta_nombre.value, "Objetivo": mo, "Actual": 0.0,
                            "Fecha_Inicio": f_inicio_input.value, "Fecha_Fin": f_fin_input.value
                        })
                        guardar_datos(db)
                        actualizar_contenido("Ahorro")
                        mostrar_alerta("¡Meta creada con éxito!")

                def eliminar_meta(i_meta):
                    if 0 <= i_meta < len(datos_user["metas"]):
                        meta_eliminada = datos_user["metas"][i_meta]["Meta"]
                        datos_user["metas"].pop(i_meta)
                        for t in datos_user["transacciones"]:
                            if t.get("Meta_Asociada") == meta_eliminada:
                                t["Meta_Asociada"] = "Ninguna"
                        recalcular_metas(datos_user)
                        guardar_datos(db)
                        actualizar_contenido("Ahorro")
                        mostrar_alerta("Meta eliminada correctamente")

                area_contenido.controls.extend([
                    logo_widget,
                    ft.Text("🎯 Gestión de Metas", size=18, weight=ft.FontWeight.BOLD),
                    meta_nombre, meta_obj, f_inicio_input, f_fin_input,
                    ft.FilledButton("Crear Meta", on_click=crear_meta),
                    ft.Divider(),
                    ft.Text("Metas Activas", size=16, weight=ft.FontWeight.BOLD)
                ])

                for idx, meta in enumerate(datos_user.get("metas", [])):
                    progreso = min(meta["Actual"] / meta["Objetivo"], 1.0) if meta["Objetivo"] > 0 else 0.0
                    
                    def crear_eliminar_meta_fn(i_m):
                        return lambda e: eliminar_meta(i_m)

                    area_contenido.controls.extend([
                        ft.Row([
                            ft.Text(f"🎯 {meta['Meta']}", weight=ft.FontWeight.BOLD, size=15),
                            ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=crear_eliminar_meta_fn(idx))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"Del {meta.get('Fecha_Inicio', 'N/A')} al {meta.get('Fecha_Fin', 'N/A')}", size=11, color="grey"),
                        ft.ProgressBar(value=progreso, width=350, color="cyan", bgcolor="#374151"),
                        ft.Text(f"Ahorrado: {formato_cop(meta['Actual'])} / {formato_cop(meta['Objetivo'])} ({progreso*100:.1f}%)", size=11),
                        ft.Divider()
                    ])

            elif seccion == "Checklist":
                ahora_bogota = datetime.now(ZoneInfo("America/Bogota"))
                hoy_str = ahora_bogota.strftime("%Y-%m-%d")
                
                ahorro_diario_actual = 0.0
                if hoy_str in datos_user["checklist"]["dias"]:
                    ahorro_diario_actual = datos_user["checklist"]["dias"][hoy_str].get("monto_dia", 0.0)
                
                inicio_semana = ahora_bogota - timedelta(days=ahora_bogota.weekday())
                ahorro_semanal_actual = 0.0
                for f_str, info in datos_user["checklist"]["dias"].items():
                    try:
                        f_dt = datetime.strptime(f_str, "%Y-%m-%d").replace(tzinfo=ZoneInfo("America/Bogota"))
                        if inicio_semana.date() <= f_dt.date() <= ahora_bogota.date():
                            ahorro_semanal_actual += info.get("monto_dia", 0.0)
                    except:
                        pass

                ahorro_mensual_actual = 0.0
                for f_str, info in datos_user["checklist"]["dias"].items():
                    try:
                        f_dt = datetime.strptime(f_str, "%Y-%m-%d")
                        if f_dt.year == ahora_bogota.year and f_dt.month == ahora_bogota.month:
                            ahorro_mensual_actual += info.get("monto_dia", 0.0)
                    except:
                        pass

                metas_p = datos_user["checklist"]["metas_periodo"]
                meta_diaria = metas_p.get("diaria", 10000.0)
                meta_semanal = metas_p.get("semanal", 50000.0)
                meta_mensual = metas_p.get("mensual", 200000.0)

                prog_diario = min(ahorro_diario_actual / meta_diaria, 1.0) if meta_diaria > 0 else 0.0
                prog_semanal = min(ahorro_semanal_actual / meta_semanal, 1.0) if meta_semanal > 0 else 0.0
                prog_mensual = min(ahorro_mensual_actual / meta_mensual, 1.0) if meta_mensual > 0 else 0.0

                fecha_ahorro_input = ft.TextField(label="Fecha (YYYY-MM-DD)", value=hoy_str, width=280)
                monto_ahorro_input = ft.TextField(label="Monto a abonar (COP $)", width=280)
                meta_destino_dropdown = ft.Dropdown(
                    label="Seleccionar Meta",
                    options=[ft.dropdown.Option(m["Meta"]) for m in datos_user.get("metas", [])],
                    width=280
                )

                def abonar_desde_checklist(e):
                    m = parsear_monto(monto_ahorro_input.value)
                    meta_sel = meta_destino_dropdown.value
                    f_ingresada = fecha_ahorro_input.value.strip() or hoy_str
                    
                    if m > 0 and meta_sel:
                        datos_user["transacciones"].append({
                            "Fecha": f_ingresada,
                            "Tipo": "Ahorro / Inversión",
                            "Categoría": "Ahorro Meta",
                            "Monto": m,
                            "Descripción": "Aporte diario desde Checklist",
                            "Meta_Asociada": meta_sel
                        })
                        if f_ingresada not in datos_user["checklist"]["dias"]:
                            datos_user["checklist"]["dias"][f_ingresada] = {"monto_dia": 0.0}
                        datos_user["checklist"]["dias"][f_ingresada]["monto_dia"] += m
                        
                        recalcular_metas(datos_user)
                        guardar_datos(db)
                        mostrar_alerta(f"¡Abono de {formato_cop(m)} agregado!")
                        monto_ahorro_input.value = ""
                        actualizar_contenido("Checklist")
                    else:
                        mostrar_alerta("Selecciona una meta y un monto válido.")

                def eliminar_registro_checklist(f_dia):
                    if f_dia in datos_user["checklist"]["dias"]:
                        del datos_user["checklist"]["dias"][f_dia]
                        guardar_datos(db)
                        actualizar_contenido("Checklist")
                        mostrar_alerta(f"Registro del {f_dia} eliminado")

                filas_check = []
                acumulado_tabla = 0.0
                for f_dia, info in sorted(datos_user["checklist"]["dias"].items()):
                    m_dia = info.get("monto_dia", 0.0)
                    acumulado_tabla += m_dia

                    def crear_eliminar_chk_fn(fd):
                        return lambda e: eliminar_registro_checklist(fd)

                    filas_check.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(f_dia)),
                            ft.DataCell(ft.Text(formato_cop(m_dia))),
                            ft.DataCell(ft.Text(formato_cop(acumulado_tabla))),
                            ft.DataCell(ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", on_click=crear_eliminar_chk_fn(f_dia)))
                        ])
                    )

                tabla_checklist = ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Fecha")), ft.DataColumn(ft.Text("Monto")),
                        ft.DataColumn(ft.Text("Total")), ft.DataColumn(ft.Text("Acción")),
                    ],
                    rows=filas_check
                )

                def exportar_pdf_chk(e):
                    try:
                        fname = generar_pdf_checklist(uname, datos_user)
                        mostrar_alerta(f"¡PDF de Checklist generado: {fname}!")
                    except Exception as ex:
                        mostrar_alerta(f"Error al generar PDF: {ex}")

                area_contenido.controls.extend([
                    logo_widget,
                    ft.Text("✅ Metas de Ahorro Periódicas", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("🌞 Meta Diaria", weight=ft.FontWeight.BOLD, color="cyan", size=12),
                            ft.ProgressBar(value=prog_diario, width=330, color="cyan", bgcolor="#374151"),
                            ft.Text(f"{formato_cop(ahorro_diario_actual)} / {formato_cop(meta_diaria)} ({prog_diario*100:.1f}%)", size=11),
                            ft.Divider(height=5),
                            ft.Text("📅 Meta Semanal", weight=ft.FontWeight.BOLD, color="cyan", size=12),
                            ft.ProgressBar(value=prog_semanal, width=330, color="blue", bgcolor="#374151"),
                            ft.Text(f"{formato_cop(ahorro_semanal_actual)} / {formato_cop(meta_semanal)} ({prog_semanal*100:.1f}%)", size=11),
                            ft.Divider(height=5),
                            ft.Text("🗓️ Meta Mensual", weight=ft.FontWeight.BOLD, color="cyan", size=12),
                            ft.ProgressBar(value=prog_mensual, width=330, color="purple", bgcolor="#374151"),
                            ft.Text(f"{formato_cop(ahorro_mensual_actual)} / {formato_cop(meta_mensual)} ({prog_mensual*100:.1f}%)", size=11),
                        ]),
                        bgcolor="#1f2937", padding=12, border_radius=8
                    ),
                    ft.Divider(),
                    ft.Text("💰 Registrar Ahorro", size=16, weight=ft.FontWeight.BOLD),
                    fecha_ahorro_input, meta_destino_dropdown, monto_ahorro_input,
                    ft.FilledButton("Abonar a la Meta", on_click=abonar_desde_checklist),
                    ft.Divider(),
                    ft.Row([
                        ft.Text("📊 Historial Checklist", size=16, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.PICTURE_AS_PDF, icon_color="cyan", on_click=exportar_pdf_chk)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([tabla_checklist], scroll=ft.ScrollMode.AUTO),
                ])

            elif seccion == "Ajustes":
                notif_config = datos_user["checklist"]["config"]
                
                input_manana = ft.TextField(label="Notificación Mañana", value=notif_config.get("mañana", ""), width=280)
                input_hora_manana = ft.TextField(label="Hora Mañana (ej. 08:00 AM)", value=notif_config.get("hora_manana", "08:00 AM"), width=280)
                input_tarde = ft.TextField(label="Notificación Tarde", value=notif_config.get("tarde", ""), width=280)
                input_hora_tarde = ft.TextField(label="Hora Tarde (ej. 02:00 PM)", value=notif_config.get("hora_tarde", "02:00 PM"), width=280)
                input_noche = ft.TextField(label="Notificación Noche", value=notif_config.get("noche", ""), width=280)
                input_hora_noche = ft.TextField(label="Hora Noche (ej. 08:00 PM)", value=notif_config.get("hora_noche", "08:00 PM"), width=280)

                def guardar_notificaciones(e):
                    notif_config["mañana"] = input_manana.value
                    notif_config["hora_manana"] = input_hora_manana.value
                    notif_config["tarde"] = input_tarde.value
                    notif_config["hora_tarde"] = input_hora_tarde.value
                    notif_config["noche"] = input_noche.value
                    notif_config["hora_noche"] = input_hora_noche.value
                    guardar_datos(db)
                    mostrar_alerta("¡Notificaciones y horarios actualizados!")

                async def probar_notificacion_nativa(e):
                    if ANDROID_NOTIF_DISPONIBLE and notifications:
                        await notifications.request_permissions()
                        await notifications.show_notification(
                            notification_id=1,
                            title="Bytepulse 🔔",
                            body=notif_config.get("mañana", "¡Revisa tus finanzas hoy!"),
                            importance="high"
                        )
                        mostrar_alerta("¡Notificación enviada a la barra del celular!")
                    else:
                        mostrar_alerta("Las notificaciones nativas solo funcionan en el APK compilado para Android.")

                area_contenido.controls.extend([
                    logo_widget,
                    ft.Text("⚙️ Ajustes del Sistema", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Usuario: {uname}", size=13),
                    ft.Text(f"Teléfono (Recuperación): {datos_user.get('telefono', 'No registrado')}", size=12, color="cyan"),
                    ft.Divider(),
                    ft.Text("🔔 Notificaciones Diarias y Horarios", size=16, weight=ft.FontWeight.BOLD),
                    input_manana, input_hora_manana,
                    ft.Divider(height=5),
                    input_tarde, input_hora_tarde,
                    ft.Divider(height=5),
                    input_noche, input_hora_noche,
                    ft.Container(height=5),
                    ft.FilledButton("Guardar Configuración", on_click=guardar_notificaciones),
                    ft.Container(height=5),
                    ft.ElevatedButton("📲 Probar Notificación en el Celular", icon=ft.Icons.NOTIFICATIONS_ACTIVE, on_click=probar_notificacion_nativa),
                    ft.Divider(),
                    ft.OutlinedButton("Cerrar Sesión", on_click=cerrar_sesion_app)
                ])

            page.update()

        def crear_opcion_menu(icon, texto, seccion):
            return ft.TextButton(
                content=ft.Row([ft.Icon(icon, size=16, color="cyan"), ft.Text(texto, size=13, color="white")], spacing=8),
                on_click=lambda e: actualizar_contenido(seccion)
            )

        sidebar.content.controls.extend([
            crear_opcion_menu(ft.Icons.DASHBOARD, "Dashboard", "Dashboard"),
            crear_opcion_menu(ft.Icons.EDIT_NOTE, "Movimientos", "Movimientos"),
            crear_opcion_menu(ft.Icons.TRACK_CHANGES, "Ahorro y Metas", "Ahorro"),
            crear_opcion_menu(ft.Icons.CHECK_BOX, "Checklist Diario", "Checklist"),
            crear_opcion_menu(ft.Icons.SETTINGS, "Ajustes", "Ajustes"),
            ft.Divider(),
            ft.OutlinedButton("Cerrar Sesión", icon=ft.Icons.LOCK, width=200, on_click=cerrar_sesion_app)
        ])

        app_bar = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.MENU, icon_color="cyan", on_click=toggle_menu),
                ft.Row([
                    obtener_imagen_segura("logo-bytepulse.png", 28, 28, 14),
                    ft.Text("BYTEPULSE", weight=ft.FontWeight.BOLD, size=14, color="cyan")
                ], spacing=6),
                ft.Container(width=40)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#111827",
            padding=10
        )

        layout_principal = ft.Stack([
            ft.Column([
                app_bar,
                ft.Container(content=area_contenido, expand=True, padding=15)
            ], expand=True),
            sidebar
        ], expand=True)

        page.add(layout_principal)
        actualizar_contenido("Dashboard")

    sesion_guardada = db.get("sesion_activa")
    if sesion_guardada and sesion_guardada in db:
        usuario_actual["nombre"] = sesion_guardada
        mostrar_dashboard_principal()
    else:
        mostrar_login()

ft.run(main)
