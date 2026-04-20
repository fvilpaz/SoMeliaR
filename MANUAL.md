# Manual de Uso — SoMeliaR 🍷

Guía completa para sumilleres y gestores de bodega.

---

## Índice

1. [Acceso y perfil de usuario](#1-acceso-y-perfil-de-usuario)
2. [Dashboard](#2-dashboard)
3. [Bodega — catálogo de vinos](#3-bodega--catálogo-de-vinos)
4. [Movimientos de stock](#4-movimientos-de-stock)
5. [Movimiento rápido](#5-movimiento-rápido)
6. [Proveedores](#6-proveedores)
7. [Pedidos](#7-pedidos)
8. [Histórico de pedidos](#8-histórico-de-pedidos)
9. [Analizar Stock con IA](#9-analizar-stock-con-ia)
10. [Anotaciones del sumiller](#10-anotaciones-del-sumiller)
11. [Herramientas (solo administrador)](#11-herramientas-solo-administrador)

---

## 1. Acceso y perfil de usuario

### Iniciar sesión
Accede con tu usuario y contraseña en la pantalla de inicio.

### Tu perfil
Haz clic en tu nombre o avatar en la parte inferior del menú lateral para acceder a tu perfil. Desde ahí puedes:

- **Cambiar tu nombre y apellidos** — aparecerán en el saludo y en los pedidos que envíes.
- **Cambiar tu email** — es la dirección desde la que figuran los pedidos.
- **Subir una foto de perfil** — aparece como avatar en el menú lateral. Si no hay foto, se muestran tus iniciales.

---

## 2. Dashboard

Pantalla de inicio con un resumen del estado actual de la bodega:

- **Resumen por familia** — número de referencias y stock total agrupado por tipo de vino (tintos nacionales, blancos, espumosos, etc.).
- **Alertas de stock mínimo** — lista de vinos cuyo stock actual está por debajo del mínimo configurado. Son los candidatos a pedir.
- **Pedidos pendientes** — acceso rápido a pedidos en estado borrador o pendiente.
- **Valor del inventario** — valor total del stock al precio de coste.
- **Gráfico de stock** — distribución visual por familia.

---

## 3. Bodega — catálogo de vinos

### Ver el catálogo
Desde el menú lateral, entra en **Bodega**. Puedes ver los vinos en dos modos:
- **Vista cuadrícula** — tarjetas con foto, stock y precio.
- **Vista lista** — tabla compacta, útil en pantallas pequeñas.

### Filtrar y buscar
- Usa los botones de familia (Tinto Nacional, Blanco, Espumoso...) para filtrar.
- Escribe en el buscador para filtrar por nombre, bodega o denominación de origen.
- Ordena por nombre, familia o stock con el desplegable.

### Ficha de un vino
Haz clic en el nombre o en el icono ✦ de una tarjeta para ver la ficha completa. Contiene:
- Todos los datos del vino (bodega, D.O., variedades, precios, ubicaciones donde se sirve).
- Historial de los últimos movimientos de stock.
- Sección de descripción generada por IA (ver apartado 9).
- Formulario para subir la foto de la botella manualmente.

### Añadir un vino nuevo
Botón **Nuevo vino** (arriba a la derecha). Rellena los datos y guarda.

### Editar un vino
Icono de lápiz en la tarjeta o en la ficha. Puedes modificar todos los datos, incluida la foto.

### Subir la foto de un vino
Desde la ficha del vino, en la sección de imagen, sube la foto de la botella o etiqueta. La imagen queda guardada en la nube y es visible para todos los usuarios.

---

## 4. Movimientos de stock

Cada entrada o salida de botellas se registra como un movimiento. El stock actual es la suma de todos los movimientos.

### Registrar un movimiento
Desde la tarjeta de un vino, pulsa **+ Movimiento**. Indica:
- **Tipo**: entrada (compra, devolución) o salida (consumo, rotura, merma).
- **Cantidad**: número de botellas.
- **Notas**: opcional, para dejar constancia del motivo.

### Stock mínimo
Cada vino puede tener configurado un stock mínimo. Cuando el stock actual cae por debajo, aparece una alerta en el dashboard y la tarjeta se marca en rojo.

---

## 5. Movimiento rápido

Accesible desde el menú lateral. Permite registrar múltiples movimientos de stock de forma ágil sin tener que entrar en la ficha de cada vino. Ideal para el cierre del día o para ajustes rápidos tras un servicio.

---

## 6. Proveedores

### Ver proveedores
Desde el menú lateral, entra en **Proveedores**. Verás la lista de distribuidores con su email de contacto.

### Añadir o editar un proveedor
Desde el listado, botón **Nuevo proveedor** o el lápiz de edición.

### Vinos asociados a un proveedor
En la ficha de cada proveedor puedes ver qué vinos suministra y a qué precio.

---

## 7. Pedidos

El flujo de un pedido tiene cuatro estados: **Borrador → Pendiente → Enviado → Recibido**.

### Crear un pedido
1. Entra en **Pedidos → Nuevo pedido**.
2. Elige el proveedor.
3. Añade las líneas de pedido: selecciona cada vino y la cantidad a pedir.
4. El pedido se guarda en estado **Borrador**.

### Revisar y confirmar
Desde la ficha del pedido, puedes editar las líneas, añadir o quitar vinos. Cuando esté listo, cámbialo a estado **Pendiente**.

### Enviar el pedido por email
Cuando el pedido está en estado Pendiente, aparece el botón **Enviar pedido**. Al pulsarlo:
1. La aplicación genera automáticamente el texto del email con el detalle de los vinos y cantidades.
2. Puedes revisar y editar el texto antes de enviarlo.
3. Confirmas el envío y el email se manda al proveedor.
4. El pedido pasa a estado **Enviado**.

> El correo se envía desde el email configurado en tu perfil de usuario. Siempre puedes ver el borrador antes de enviarlo, nunca se manda sin tu confirmación.

### Registrar la recepción
Cuando llegue la mercancía, entra en el pedido y pulsa **Marcar como recibido**. El sistema registra automáticamente las entradas de stock para cada vino del pedido.

---

## 8. Histórico de pedidos

Accesible desde **Histórico** en el menú lateral. Muestra todos los pedidos completados (estado Recibido) organizados por fecha. Puedes desplegar cada pedido para ver su detalle.

---

## 9. Analizar Stock con IA

Desde el menú lateral, **Analizar Stock (IA)**. La aplicación utiliza inteligencia artificial (Google Gemini) para:

- Analizar el stock actual de todos los vinos.
- Detectar qué referencias están próximas al mínimo o agotadas.
- Sugerir qué pedir y en qué cantidades, teniendo en cuenta el histórico de consumo.
- Generar un borrador de pedido automático que puedes revisar y ajustar antes de enviar.

### Descripción de un vino con IA
En la ficha de cada vino, el botón **Generar descripción** crea automáticamente una descripción de cata en español para ese vino. La descripción se guarda y no es necesario regenerarla cada vez (aunque puedes forzar una nueva si quieres actualizarla).

---

## 10. Anotaciones del sumiller

Accesible desde **Anotaciones** en el menú lateral. Espacio para dejar notas rápidas: incidencias, recordatorios, observaciones sobre un servicio.

- **Nueva anotación**: escribe el texto y elige la prioridad (normal, alta).
- **Dictado por voz**: pulsa el icono del micrófono para dictar la anotación con la voz (requiere permiso del navegador).
- **Resolver**: marca una anotación como resuelta para archivarla.
- **Eliminar**: borra una anotación que ya no es necesaria.

---

## 11. Herramientas (solo administrador)

Esta sección solo es visible para usuarios con rol de administrador (superusuario).

### Importar desde Excel
Sube el **Libro de Bodega** en formato `.xls` o `.xlsx`. El sistema importa automáticamente:
- Todos los vinos con sus datos (nombre, bodega, D.O., precios, etc.).
- Proveedores y relación con los vinos.
- Stock inicial de cada referencia.

> Si ya hay datos en el sistema, la importación los añade encima. Si quieres empezar desde cero, usa primero la opción **Limpiar base de datos**.

### Logo del sidebar
Sube una imagen cuadrada (mínimo 200×200 px) que aparecerá en el menú lateral en lugar del logo por defecto. Recomendado: el logo del hotel o del departamento de F&B.

### Imagen de login
Sube la foto que aparece como logo circular en la pantalla de inicio de sesión.

### Limpiar base de datos
Elimina **todos los vinos, movimientos, proveedores, pedidos y anotaciones**. Los usuarios no se borran. Úsalo solo si vas a reimportar un Excel completamente nuevo.

> Esta acción no se puede deshacer. El sistema pedirá confirmación antes de ejecutarla.

---

## Preguntas frecuentes

**¿Puedo usar la app desde el móvil?**
Sí. El diseño es completamente responsive. En móvil, el menú lateral se abre con el botón de las tres rayas (☰) en la esquina superior izquierda.

**¿Las fotos de los vinos se pierden si se actualiza el sistema?**
No. Las imágenes se almacenan en Cloudinary, un servicio externo. No dependen del servidor y persisten siempre.

**¿Quién recibe el email del pedido?**
El email del pedido se envía a la dirección del proveedor configurada en su ficha. El remitente es el usuario que realiza el envío.

**¿Qué pasa si el análisis de IA no está disponible?**
Si no hay conexión o la API de Gemini no responde, el sistema mostrará un mensaje de error y podrás gestionar el pedido manualmente.

**¿Cómo configuro el stock mínimo de un vino?**
Desde la ficha del vino, en la sección de edición, encontrarás el campo **Stock mínimo**. Cuando el stock caiga por debajo de ese valor, aparecerá una alerta en el dashboard.

---

*Manual elaborado para SoMeliaR — Meliá Hotels International.*
*Desarrollado por Fernando Vilas Paz.*
