"""Carga datos de demostración realistas para SoMeliaR."""
from django.core.management.base import BaseCommand
from bodega.models import Vino, Movimiento, StockConfig
from proveedores.models import Proveedor, VinoProveedor


class Command(BaseCommand):
    help = "Carga datos de demostración: vinos, proveedores, stock y movimientos"

    def handle(self, *args, **options):
        self.stdout.write("Cargando datos demo...")

        # Proveedores
        prov1 = Proveedor.objects.create(
            nombre="Bodegas Torres Distribución",
            email="pedidos@torres.es",
            telefono="934 000 100",
            contacto="Marta López",
        )
        prov2 = Proveedor.objects.create(
            nombre="Vinos Selectos del Sur",
            email="comercial@vinosselectos.es",
            telefono="956 123 456",
            contacto="Antonio García",
        )
        prov3 = Proveedor.objects.create(
            nombre="Distribuciones Rioja Premium",
            email="pedidos@riojapremium.es",
            telefono="941 234 567",
            contacto="Javier Martínez",
        )

        # Vinos con datos realistas
        vinos_data = [
            # Blancos
            {"nombre": "Albariño Pazo Señoráns", "anada": 2024, "familia": "blanco",
             "denominacion_origen": "Rías Baixas", "precio_coste": 8.50, "precio_carta": 28,
             "prov": prov1, "precio_prov": 8.50, "stock_ini": 18, "minimo": 6, "optimo": 24},
            {"nombre": "Verdejo Rueda Marqués de Riscal", "anada": 2024, "familia": "blanco",
             "denominacion_origen": "Rueda", "precio_coste": 5.20, "precio_carta": 18,
             "prov": prov1, "precio_prov": 5.20, "stock_ini": 24, "minimo": 12, "optimo": 36},
            {"nombre": "Viña Sol Torres", "anada": 2024, "familia": "blanco",
             "denominacion_origen": "Catalunya", "precio_coste": 3.80, "precio_carta": 14,
             "prov": prov1, "precio_prov": 3.80, "stock_ini": 30, "minimo": 12, "optimo": 36},
            # Tintos
            {"nombre": "Protos Crianza", "anada": 2021, "familia": "tinto",
             "denominacion_origen": "Ribera del Duero", "precio_coste": 9.00, "precio_carta": 32,
             "prov": prov3, "precio_prov": 9.00, "stock_ini": 4, "minimo": 6, "optimo": 18},
            {"nombre": "Marqués de Murrieta Reserva", "anada": 2019, "familia": "tinto",
             "denominacion_origen": "Rioja", "precio_coste": 12.50, "precio_carta": 42,
             "prov": prov3, "precio_prov": 12.50, "stock_ini": 8, "minimo": 6, "optimo": 12},
            {"nombre": "Ramón Bilbao Crianza", "anada": 2021, "familia": "tinto",
             "denominacion_origen": "Rioja", "precio_coste": 6.00, "precio_carta": 22,
             "prov": prov3, "precio_prov": 6.00, "stock_ini": 3, "minimo": 12, "optimo": 24},
            {"nombre": "Pesquera Crianza", "anada": 2020, "familia": "tinto",
             "denominacion_origen": "Ribera del Duero", "precio_coste": 11.00, "precio_carta": 38,
             "prov": prov3, "precio_prov": 11.00, "stock_ini": 10, "minimo": 6, "optimo": 12},
            # Rosados
            {"nombre": "Muga Rosado", "anada": 2024, "familia": "rosado",
             "denominacion_origen": "Rioja", "precio_coste": 5.50, "precio_carta": 20,
             "prov": prov3, "precio_prov": 5.50, "stock_ini": 2, "minimo": 6, "optimo": 18},
            {"nombre": "Chivite Gran Feudo Rosado", "anada": 2024, "familia": "rosado",
             "denominacion_origen": "Navarra", "precio_coste": 4.00, "precio_carta": 16,
             "prov": prov1, "precio_prov": 4.00, "stock_ini": 12, "minimo": 6, "optimo": 18},
            # Espumosos
            {"nombre": "Codorníu Anna de Codorníu", "anada": None, "familia": "espumoso",
             "denominacion_origen": "Cava", "precio_coste": 7.00, "precio_carta": 26,
             "prov": prov1, "precio_prov": 7.00, "stock_ini": 1, "minimo": 6, "optimo": 18},
            {"nombre": "Freixenet Cordón Negro", "anada": None, "familia": "espumoso",
             "denominacion_origen": "Cava", "precio_coste": 4.50, "precio_carta": 18,
             "prov": prov1, "precio_prov": 4.50, "stock_ini": 15, "minimo": 12, "optimo": 24},
            # Generosos
            {"nombre": "Tío Pepe Fino", "anada": None, "familia": "generoso",
             "denominacion_origen": "Jerez", "precio_coste": 5.00, "precio_carta": 18,
             "prov": prov2, "precio_prov": 5.00, "stock_ini": 8, "minimo": 6, "optimo": 12},
            {"nombre": "Lustau Manzanilla Papirusa", "anada": None, "familia": "generoso",
             "denominacion_origen": "Sanlúcar de Barrameda", "precio_coste": 6.50, "precio_carta": 22,
             "prov": prov2, "precio_prov": 6.50, "stock_ini": 5, "minimo": 6, "optimo": 12},
            # Dulces
            {"nombre": "Jorge Ordóñez Nº1 Selección Especial", "anada": 2022, "familia": "dulce",
             "denominacion_origen": "Málaga", "precio_coste": 10.00, "precio_carta": 35,
             "prov": prov2, "precio_prov": 10.00, "stock_ini": 6, "minimo": 4, "optimo": 8},
        ]

        for data in vinos_data:
            vino = Vino.objects.create(
                nombre=data["nombre"],
                anada=data["anada"],
                familia=data["familia"],
                denominacion_origen=data["denominacion_origen"],
                precio_coste=data["precio_coste"],
                precio_carta=data["precio_carta"],
            )
            StockConfig.objects.create(
                vino=vino,
                stock_minimo=data["minimo"],
                stock_optimo=data["optimo"],
            )
            VinoProveedor.objects.create(
                vino=vino,
                proveedor=data["prov"],
                precio=data["precio_prov"],
                es_principal=True,
            )
            # Movimiento de entrada inicial
            Movimiento.objects.create(
                vino=vino,
                tipo=Movimiento.Tipo.ENTRADA,
                cantidad=data["stock_ini"],
                notas="Stock inicial demo",
            )

        total = Vino.objects.count()
        bajo = sum(1 for v in Vino.objects.all() if v.bajo_minimo)
        self.stdout.write(self.style.SUCCESS(
            f"✓ Demo cargada: {total} vinos, {Proveedor.objects.count()} proveedores, "
            f"{bajo} vinos bajo mínimo"
        ))
