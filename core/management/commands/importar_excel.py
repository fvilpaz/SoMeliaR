"""Importa los datos reales del Libro de Bodega desde el Excel."""
import re
from decimal import Decimal, InvalidOperation

import xlrd
from django.core.management.base import BaseCommand

from bodega.models import Movimiento, StockConfig, Vino
from proveedores.models import Proveedor, VinoProveedor
from pedidos.models import Pedido, LineaPedido


# Mapeo de las cabeceras de sección en la hoja maestra → familia
SECCIONES = {
    "Burbujas Nacional": Vino.Familia.ESPUMOSO_NAC,
    "Burbujas Internacional (Champagne)": Vino.Familia.CHAMPAGNE,
    "Burbujas Internacional (Otros)": Vino.Familia.ESPUMOSO_INT,
    "Blanco Nacional": Vino.Familia.BLANCO_NAC,
    "Blanco Internacional": Vino.Familia.BLANCO_INT,
    "Tintos Nacional": Vino.Familia.TINTO_NAC,
    "Tintos Internacional": Vino.Familia.TINTO_INT,
    "Grandes Vinos Tintos de España": Vino.Familia.GRANDES_TINTOS,
    "Rosados": Vino.Familia.ROSADO,
    "Dulces": Vino.Familia.DULCE,
    "Generosos": Vino.Familia.GENEROSO,
    "Fuera de Carta": Vino.Familia.FUERA_CARTA,
    "Vinos de Propiedad": Vino.Familia.PROPIEDAD,
}

# Hojas de proveedor con su nombre normalizado
HOJAS_PROVEEDOR = {
    "Coupa": "Coupa (Economato Meliá)",
    "Sanchez Polo": "Sánchez Polo",
    "Vila Viniteca": "Vila Viniteca",
    "LVMH": "LVMH (Moët Hennessy)",
    "Terroir Champenoise": "Terroir Champenoise",
    "Vega Tolosa": "Vega Tolosa",
    "Decantare": "Decantare",
    "Don Pepe": "Don Pepe",
    "Hibeta": "Hibeta",
    "Le Tribute (Pebar)": "Le Tribute (Pebar)",
    "Lopez Pardo": "López Pardo",
    "Narbona Solis": "Narbona Solís",
    "Vadevinos Exclusivas": "Vadevinos Exclusivas",
}


def safe_decimal(val, default="0"):
    """Convierte un valor a Decimal de forma segura."""
    if val == "" or val is None:
        return Decimal(default)
    try:
        return Decimal(str(val)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def safe_int(val):
    """Convierte un valor a int de forma segura."""
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def safe_stock(val):
    """Convierte stock a Decimal con 1 decimal."""
    if val == "" or val is None:
        return None
    try:
        return Decimal(str(val)).quantize(Decimal("0.1"))
    except (InvalidOperation, ValueError):
        return None


def limpiar_nombre(nombre):
    """Limpia el nombre del vino de notas como (muestra), AGOTADO, etc."""
    nombre = nombre.strip()
    # No limpiar demasiado, conservar la info
    return nombre


class Command(BaseCommand):
    help = "Importa datos del Libro de Bodega Excel"

    def add_arguments(self, parser):
        parser.add_argument(
            "archivo",
            help="Ruta al archivo .xls del Libro de Bodega",
        )

    def handle(self, *args, **options):
        path = options["archivo"]
        wb = xlrd.open_workbook(path)

        self.stdout.write("=" * 60)
        self.stdout.write("IMPORTADOR DE LIBRO DE BODEGA")
        self.stdout.write("=" * 60)

        # 1. Importar proveedores desde las hojas de proveedor
        proveedores = self._importar_proveedores(wb)

        # 2. Importar vinos desde la hoja maestra
        vinos_map = self._importar_vinos(wb)

        # 3. Vincular vinos con proveedores y crear stock
        self._vincular_proveedores(wb, vinos_map, proveedores)

        # 4. Marcar vinos por copas
        self._marcar_copas(wb, vinos_map)

        # 5. Importar pedidos pendientes
        self._importar_pedidos(wb, vinos_map, proveedores)

        # 6. Crear superusuario
        self._crear_admin()

        # Resumen
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS(
            f"✓ {Vino.objects.count()} vinos importados"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"✓ {Proveedor.objects.count()} proveedores"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"✓ {Movimiento.objects.count()} movimientos de stock"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"✓ {Vino.objects.filter(es_copa=True).count()} vinos por copas"
        ))
        bajo = sum(1 for v in Vino.objects.all() if v.bajo_minimo)
        self.stdout.write(self.style.SUCCESS(
            f"✓ {bajo} vinos bajo mínimo"
        ))
        pedidos = Pedido.objects.count()
        if pedidos:
            self.stdout.write(self.style.SUCCESS(
                f"✓ {pedidos} pedidos pendientes importados"
            ))

    def _importar_proveedores(self, wb):
        """Crea proveedores a partir de las hojas de proveedor."""
        self.stdout.write("\n--- Importando proveedores ---")
        proveedores = {}

        for hoja_nombre, nombre_normalizado in HOJAS_PROVEEDOR.items():
            if hoja_nombre not in wb.sheet_names():
                continue
            sh = wb.sheet_by_name(hoja_nombre)
            if sh.nrows < 2:
                continue

            # Buscar contacto en la primera fila de datos
            email = ""
            telefono = ""
            contacto = ""
            for r in range(1, min(sh.nrows, 5)):
                e = str(sh.cell_value(r, 10)).strip() if sh.ncols > 10 else ""
                if e and "@" in e:
                    email = e
                    contacto = str(sh.cell_value(r, 9)).strip() if sh.ncols > 9 else ""
                    tel = sh.cell_value(r, 11) if sh.ncols > 11 else ""
                    if tel:
                        telefono = str(int(tel)) if isinstance(tel, float) else str(tel)
                    break

            prov = Proveedor.objects.create(
                nombre=nombre_normalizado,
                email=email,
                telefono=telefono,
                contacto=contacto,
            )
            proveedores[hoja_nombre] = prov
            self.stdout.write(f"  {nombre_normalizado} ({email})")

        return proveedores

    def _importar_vinos(self, wb):
        """Importa vinos de la hoja maestra 'Cañitas Maite (M)'."""
        self.stdout.write("\n--- Importando vinos ---")
        sh = wb.sheet_by_name("Cañitas Maite (M)")

        vinos_map = {}  # nombre → Vino
        familia_actual = Vino.Familia.ESPUMOSO_NAC  # default primera sección
        count = 0

        for r in range(1, sh.nrows):  # skip header
            nombre = str(sh.cell_value(r, 1)).strip()
            if not nombre or nombre == "TOTAL (sin IVA / con IVA)":
                continue

            # Detectar cabeceras de sección
            stock_val = sh.cell_value(r, 7)
            precio_val = sh.cell_value(r, 6)
            distribuidor = str(sh.cell_value(r, 9)).strip()

            es_seccion = False
            for seccion_nombre, seccion_familia in SECCIONES.items():
                if nombre == seccion_nombre or nombre.startswith(seccion_nombre):
                    familia_actual = seccion_familia
                    es_seccion = True
                    break

            if es_seccion:
                continue

            # Es un vino real
            bodega = str(sh.cell_value(r, 2)).strip()
            azucar = str(sh.cell_value(r, 3)).strip()
            do = str(sh.cell_value(r, 4)).strip()
            variedades = str(sh.cell_value(r, 5)).strip()
            precio_coste = safe_decimal(precio_val)
            precio_carta_raw = sh.cell_value(r, 8)
            precio_carta = safe_decimal(precio_carta_raw)
            stock = safe_stock(stock_val)

            # Ubicaciones
            canitas_val = str(sh.cell_value(r, 10)).strip().upper()
            ene_val = str(sh.cell_value(r, 11)).strip().upper()
            pool_val = str(sh.cell_value(r, 12)).strip().upper()

            en_canitas = canitas_val in ("C", "B", "C-B")
            en_ene = bool(ene_val) and ene_val not in ("", "0")
            en_pool = pool_val in ("C", "OPCIONAL") or bool(pool_val and pool_val not in ("", "0"))

            # Determinar si va por Coupa
            via_coupa = distribuidor.lower() == "coupa"

            # Limpiar nombre
            nombre_limpio = limpiar_nombre(nombre)

            # Evitar duplicados por nombre
            if nombre_limpio in vinos_map:
                continue

            vino = Vino.objects.create(
                nombre=nombre_limpio,
                bodega_nombre=bodega,
                familia=familia_actual,
                azucar=azucar,
                denominacion_origen=do,
                variedades=variedades,
                precio_coste=precio_coste,
                precio_carta=precio_carta,
                via_coupa=via_coupa,
                en_canitas=en_canitas,
                en_ene=en_ene,
                en_pool=en_pool,
            )

            vinos_map[nombre_limpio] = vino

            # Crear movimiento de stock si hay stock
            if stock is not None and stock > 0:
                Movimiento.objects.create(
                    vino=vino,
                    tipo=Movimiento.Tipo.ENTRADA,
                    cantidad=stock,
                    notas="Stock importado del Libro de Bodega",
                )

            # Crear StockConfig con defaults razonables
            StockConfig.objects.create(
                vino=vino,
                stock_minimo=6 if precio_coste < 50 else 2,
                stock_optimo=12 if precio_coste < 50 else 4,
            )

            # Vincular con distribuidor de la hoja maestra
            if distribuidor and distribuidor.lower() != "coupa":
                # Lo vincularemos en _vincular_proveedores
                vino._distribuidor_nombre = distribuidor
            else:
                vino._distribuidor_nombre = distribuidor

            count += 1

        self.stdout.write(f"  {count} vinos importados")
        return vinos_map

    def _vincular_proveedores(self, wb, vinos_map, proveedores):
        """Vincula vinos con proveedores usando las hojas de proveedor."""
        self.stdout.write("\n--- Vinculando vinos con proveedores ---")
        count = 0

        for hoja_nombre, prov in proveedores.items():
            if hoja_nombre not in wb.sheet_names():
                continue
            sh = wb.sheet_by_name(hoja_nombre)

            for r in range(1, sh.nrows):
                nombre = str(sh.cell_value(r, 1)).strip()
                if not nombre or nombre == "TOTAL (sin IVA / con IVA)":
                    continue

                nombre_limpio = limpiar_nombre(nombre)
                vino = vinos_map.get(nombre_limpio)
                if not vino:
                    # Intentar buscar por nombre parcial
                    for key, v in vinos_map.items():
                        if nombre_limpio.lower() in key.lower() or key.lower() in nombre_limpio.lower():
                            vino = v
                            break

                if not vino:
                    continue

                precio = safe_decimal(sh.cell_value(r, 4) if sh.ncols > 4 else 0)

                # Evitar duplicados
                if not VinoProveedor.objects.filter(vino=vino, proveedor=prov).exists():
                    VinoProveedor.objects.create(
                        vino=vino,
                        proveedor=prov,
                        precio=precio,
                        es_principal=True,
                    )
                    count += 1

        self.stdout.write(f"  {count} vínculos vino-proveedor creados")

    def _marcar_copas(self, wb, vinos_map):
        """Marca vinos que se venden por copas desde la hoja 'Vinos a Copas'."""
        self.stdout.write("\n--- Marcando vinos por copas ---")

        if "Vinos a Copas" not in wb.sheet_names():
            self.stdout.write("  Hoja 'Vinos a Copas' no encontrada")
            return

        sh = wb.sheet_by_name("Vinos a Copas")
        count = 0

        for r in range(1, sh.nrows):
            nombre = str(sh.cell_value(r, 1)).strip()
            if not nombre or nombre == "TOTAL (sin IVA / con IVA)":
                continue

            precio_copa = safe_decimal(sh.cell_value(r, 8) if sh.ncols > 8 else 0)
            nombre_limpio = limpiar_nombre(nombre)

            vino = vinos_map.get(nombre_limpio)
            if not vino:
                for key, v in vinos_map.items():
                    if nombre_limpio.lower() in key.lower() or key.lower() in nombre_limpio.lower():
                        vino = v
                        break

            if vino:
                vino.es_copa = True
                vino.precio_copa = precio_copa
                vino.save()
                count += 1

        self.stdout.write(f"  {count} vinos marcados como copa")

    def _importar_pedidos(self, wb, vinos_map, proveedores):
        """Importa pedidos pendientes desde las hojas de proveedor."""
        self.stdout.write("\n--- Importando pedidos pendientes ---")

        for hoja_nombre, prov in proveedores.items():
            if hoja_nombre not in wb.sheet_names():
                continue
            sh = wb.sheet_by_name(hoja_nombre)

            lineas_pedido = []
            for r in range(1, sh.nrows):
                nombre = str(sh.cell_value(r, 1)).strip()
                if not nombre or nombre == "TOTAL (sin IVA / con IVA)":
                    continue

                # Columna "Pedido" (col 3)
                pedido_val = sh.cell_value(r, 3) if sh.ncols > 3 else ""
                if not pedido_val or pedido_val == "":
                    continue

                try:
                    cantidad = int(float(pedido_val))
                except (ValueError, TypeError):
                    continue

                if cantidad <= 0:
                    continue

                nombre_limpio = limpiar_nombre(nombre)
                vino = vinos_map.get(nombre_limpio)
                if not vino:
                    for key, v in vinos_map.items():
                        if nombre_limpio.lower() in key.lower() or key.lower() in nombre_limpio.lower():
                            vino = v
                            break

                if not vino:
                    continue

                precio = safe_decimal(sh.cell_value(r, 4) if sh.ncols > 4 else 0)
                lineas_pedido.append({
                    "vino": vino,
                    "cantidad": cantidad,
                    "precio": precio,
                })

            if lineas_pedido:
                pedido = Pedido.objects.create(
                    proveedor=prov,
                    estado=Pedido.Estado.BORRADOR,
                    generado_por_ia=False,
                    notas=f"Pedido importado del Libro de Bodega (hoja {hoja_nombre})",
                )
                for lp in lineas_pedido:
                    LineaPedido.objects.create(
                        pedido=pedido,
                        vino=lp["vino"],
                        cantidad_sugerida=lp["cantidad"],
                        precio_unitario=lp["precio"],
                    )
                self.stdout.write(
                    f"  Pedido {prov.nombre}: {len(lineas_pedido)} líneas"
                )

    def _crear_admin(self):
        """Crea superusuario admin si no existe."""
        from django.contrib.auth.models import User
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@someliar.demo", "admin")
            self.stdout.write("\n  Superusuario creado: admin / admin")
