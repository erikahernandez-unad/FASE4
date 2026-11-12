#   Trabajo colaborativo Fase 4-UNAD.
"""
Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas.
Curso: Programación (213023) - UNAD - Fase 4.
"""

from abc import ABC, abstractmethod
import logging
import math
import re


# Los eventos y errores se almacenan en un archivo local, sin base de datos.
logging.basicConfig(
    filename="logs_software_fj.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("SoftwareFJ")


class SoftwareFJError(Exception):
    """Excepción base del sistema."""


class ClienteInvalidoError(SoftwareFJError):
    """Error en los datos de un cliente."""


class ServicioInvalidoError(SoftwareFJError):
    """Error en los datos o parámetros de un servicio."""


class ServicioNoDisponibleError(SoftwareFJError):
    """El servicio no se encuentra disponible."""


class ReservaInvalidaError(SoftwareFJError):
    """Error en la creación o configuración de una reserva."""


class OperacionNoPermitidaError(SoftwareFJError):
    """La operación no está permitida para el estado actual."""


class CalculoInconsistenteError(SoftwareFJError):
    """Error en el cálculo del costo."""


def _validar_identificador(valor):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("El identificador es obligatorio y debe ser texto.")
    return valor.strip()


def _validar_numero(valor, nombre, minimo=None, maximo=None):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{nombre} debe ser un número.")
    if not math.isfinite(valor):
        raise ValueError(f"{nombre} debe ser un número finito.")
    if minimo is not None and valor < minimo:
        raise ValueError(f"{nombre} debe ser mayor o igual a {minimo}.")
    if maximo is not None and valor > maximo:
        raise ValueError(f"{nombre} debe ser menor o igual a {maximo}.")
    return valor


class EntidadBase(ABC):
    """Clase abstracta para las entidades del sistema."""

    def __init__(self, identificador):
        self._identificador = _validar_identificador(identificador)

    @property
    def identificador(self):
        return self._identificador

    @abstractmethod
    def describir(self):
        """Devuelve una descripción de la entidad."""


class Cliente(EntidadBase):
    """Cliente con datos personales encapsulados y validados."""

    def __init__(self, identificador, nombre, documento, correo, telefono):
        super().__init__(identificador)
        try:
            self.nombre = nombre
            self.documento = documento
            self.correo = correo
            self.telefono = telefono
        except ValueError as error:
            raise ClienteInvalidoError(
                f"No se pudo crear el cliente '{identificador}': {error}"
            ) from error

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ValueError("El nombre debe contener al menos 3 caracteres.")
        self.__nombre = valor.strip()

    @property
    def documento(self):
        return self.__documento

    @documento.setter
    def documento(self, valor):
        if valor is None or not re.fullmatch(r"\d{6,12}", str(valor)):
            raise ValueError("El documento debe tener entre 6 y 12 dígitos.")
        self.__documento = str(valor)

    @property
    def correo(self):
        return self.__correo

    @correo.setter
    def correo(self, valor):
        if not isinstance(valor, str):
            raise ValueError("El correo electrónico debe ser texto.")
        valor = valor.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
            raise ValueError("El correo electrónico no tiene un formato válido.")
        self.__correo = valor

    @property
    def telefono(self):
        return self.__telefono

    @telefono.setter
    def telefono(self, valor):
        if valor is None or not re.fullmatch(r"\d{10}", str(valor)):
            raise ValueError("El teléfono debe tener exactamente 10 dígitos.")
        self.__telefono = str(valor)

    def describir(self):
        return (
            f"Cliente {self.identificador}: {self.nombre} "
            f"(Doc: {self.documento})"
        )


class Servicio(EntidadBase, ABC):
    """Clase abstracta para los servicios ofrecidos por Software FJ."""

    def __init__(self, identificador, nombre, tarifa_hora, disponible=True):
        super().__init__(identificador)
        if not isinstance(nombre, str) or not nombre.strip():
            raise ServicioInvalidoError("El nombre del servicio es obligatorio.")
        try:
            _validar_numero(tarifa_hora, "La tarifa por hora", minimo=0.01)
        except ValueError as error:
            raise ServicioInvalidoError(str(error)) from error
        if not isinstance(disponible, bool):
            raise ServicioInvalidoError("La disponibilidad debe ser booleana.")
        self._nombre = nombre.strip()
        self._tarifa_hora = float(tarifa_hora)
        self._disponible = disponible

    @property
    def nombre(self):
        return self._nombre

    @property
    def tarifa_hora(self):
        return self._tarifa_hora

    @property
    def disponible(self):
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        if not isinstance(valor, bool):
            raise ServicioInvalidoError("La disponibilidad debe ser booleana.")
        self._disponible = valor

    @abstractmethod
    def validar_parametros(self, duracion):
        """Valida los parámetros propios del servicio."""

    @abstractmethod
    def calcular_costo_base(self, duracion):
        """Calcula el costo antes de impuestos y descuentos."""

    @abstractmethod
    def describir(self):
        """Describe el servicio."""

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        """
        Calcula el costo en distintas modalidades mediante parámetros opcionales.

        Variantes admitidas:
        - calcular_costo(duracion)
        - calcular_costo(duracion, impuesto)
        - calcular_costo(duracion, impuesto, descuento)

        Python no admite sobrecarga tradicional por firma; por eso se
        implementan las variantes mediante parámetros opcionales.
        """
        try:
            _validar_numero(impuesto, "El impuesto", minimo=0, maximo=1)
            _validar_numero(descuento, "El descuento", minimo=0, maximo=1)
            self.validar_parametros(duracion)
            base = self.calcular_costo_base(duracion)
            _validar_numero(base, "El costo base", minimo=0)
            total = base * (1 - descuento) * (1 + impuesto)
            _validar_numero(total, "El costo total", minimo=0)
            return round(total, 2)
        except (ValueError, TypeError, ServicioInvalidoError) as error:
            raise CalculoInconsistenteError(
                f"No fue posible calcular el costo: {error}"
            ) from error

    def calcular_costo_con_impuesto(self, duracion, impuesto):
        """Variante de cálculo que aplica únicamente impuesto."""
        return self.calcular_costo(duracion, impuesto=impuesto)

    def calcular_costo_con_descuento(self, duracion, descuento):
        """Variante de cálculo que aplica únicamente descuento."""
        return self.calcular_costo(duracion, descuento=descuento)

    def calcular_costo_completo(self, duracion, impuesto, descuento):
        """Variante de cálculo que aplica impuesto y descuento."""
        return self.calcular_costo(
            duracion, impuesto=impuesto, descuento=descuento
        )


class ReservaSala(Servicio):
    """Servicio de reserva de salas."""

    def __init__(self, identificador, nombre, tarifa_hora, capacidad, disponible=True):
        super().__init__(identificador, nombre, tarifa_hora, disponible)
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:
            raise ServicioInvalidoError(
                "La capacidad de la sala debe ser un entero mayor a 0."
            )
        self._capacidad = capacidad

    @property
    def capacidad(self):
        return self._capacidad

    def validar_parametros(self, duracion):
        try:
            _validar_numero(duracion, "La duración", minimo=1, maximo=8)
        except ValueError as error:
            raise ServicioInvalidoError(
                "La sala se reserva entre 1 y 8 horas."
            ) from error

    def calcular_costo_base(self, duracion):
        return self._tarifa_hora * duracion

    def describir(self):
        return (
            f"Sala '{self.nombre}' (capacidad {self._capacidad}) - "
            f"${self._tarifa_hora:,.0f}/hora"
        )


class AlquilerEquipo(Servicio):
    """Servicio de alquiler de equipos."""

    DEPOSITO = 20000.0

    def __init__(
        self, identificador, nombre, tarifa_hora, tipo_equipo, disponible=True
    ):
        super().__init__(identificador, nombre, tarifa_hora, disponible)
        if not isinstance(tipo_equipo, str) or not tipo_equipo.strip():
            raise ServicioInvalidoError("El tipo de equipo es obligatorio.")
        self._tipo_equipo = tipo_equipo.strip()

    @property
    def tipo_equipo(self):
        return self._tipo_equipo

    def validar_parametros(self, duracion):
        try:
            _validar_numero(duracion, "La duración", minimo=1, maximo=72)
        except ValueError as error:
            raise ServicioInvalidoError(
                "El equipo se alquila entre 1 y 72 horas."
            ) from error

    def calcular_costo_base(self, duracion):
        return self._tarifa_hora * duracion + self.DEPOSITO

    def describir(self):
        return (
            f"Alquiler de {self._tipo_equipo} '{self.nombre}' - "
            f"${self._tarifa_hora:,.0f}/hora + depósito"
        )


class AsesoriaEspecializada(Servicio):
    """Servicio de asesorías especializadas."""

    RECARGOS = {"junior": 1.0, "senior": 1.25, "experto": 1.5}

    def __init__(self, identificador, nombre, tarifa_hora, nivel, disponible=True):
        super().__init__(identificador, nombre, tarifa_hora, disponible)
        if not isinstance(nivel, str) or nivel.lower() not in self.RECARGOS:
            raise ServicioInvalidoError(
                f"Nivel inválido. Opciones: {list(self.RECARGOS)}"
            )
        self._nivel = nivel.lower()

    @property
    def nivel(self):
        return self._nivel

    def validar_parametros(self, duracion):
        try:
            _validar_numero(duracion, "La duración", minimo=1, maximo=4)
        except ValueError as error:
            raise ServicioInvalidoError(
                "La asesoría dura entre 1 y 4 horas."
            ) from error

    def calcular_costo_base(self, duracion):
        return self._tarifa_hora * duracion * self.RECARGOS[self._nivel]

    def describir(self):
        return (
            f"Asesoría '{self.nombre}' nivel {self._nivel} - "
            f"${self._tarifa_hora:,.0f}/hora"
        )


class Reserva(EntidadBase):
    """Integra cliente, servicio, duración y estado."""

    ESTADOS = ("PENDIENTE", "CONFIRMADA", "CANCELADA", "PROCESADA")

    def __init__(self, identificador, cliente, servicio, duracion):
        super().__init__(identificador)
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un servicio válido.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{servicio.nombre}' no está disponible."
            )
        try:
            servicio.validar_parametros(duracion)
        except ServicioInvalidoError as error:
            raise ReservaInvalidaError(
                f"Duración inválida para la reserva: {error}"
            ) from error
        self.__cliente = cliente
        self.__servicio = servicio
        self.__duracion = duracion
        self.__estado = "PENDIENTE"

    @property
    def cliente(self):
        return self.__cliente

    @property
    def servicio(self):
        return self.__servicio

    @property
    def duracion(self):
        return self.__duracion

    @property
    def estado(self):
        return self.__estado

    def confirmar(self):
        if self.__estado != "PENDIENTE":
            raise OperacionNoPermitidaError(
                f"No se puede confirmar una reserva {self.__estado}."
            )
        if not self.__servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self.__servicio.nombre}' ya no está disponible."
            )
        self.__estado = "CONFIRMADA"
        logger.info("Reserva confirmada: %s", self.identificador)

    def cancelar(self):
        if self.__estado in ("CANCELADA", "PROCESADA"):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar una reserva {self.__estado}."
            )
        self.__estado = "CANCELADA"
        logger.info("Reserva cancelada: %s", self.identificador)

    def procesar(self, impuesto=0.0, descuento=0.0):
        try:
            if self.__estado != "CONFIRMADA":
                raise OperacionNoPermitidaError(
                    "Solo se procesan reservas CONFIRMADAS."
                )
            if not self.__servicio.disponible:
                raise ServicioNoDisponibleError(
                    f"El servicio '{self.__servicio.nombre}' no está disponible."
                )
            costo = self.__servicio.calcular_costo(
                self.__duracion, impuesto, descuento
            )
        except SoftwareFJError as error:
            logger.exception(
                "Fallo al procesar reserva %s", self.identificador
            )
            raise OperacionNoPermitidaError(
                f"Reserva {self.identificador} no procesada: {error}"
            ) from error
        else:
            self.__estado = "PROCESADA"
            logger.info(
                "Reserva %s procesada. Total: %.2f", self.identificador, costo
            )
            return costo
        finally:
            logger.info(
                "Finalizó el intento de procesamiento de la reserva %s",
                self.identificador,
            )

    def describir(self):
        return (
            f"Reserva {self.identificador} [{self.estado}] - "
            f"{self.cliente.nombre} - {self.servicio.nombre} - {self.duracion}h"
        )


class GestorFJ:
    """Administra clientes, servicios y reservas mediante listas internas."""

    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []

    @staticmethod
    def _id_existe(elementos, identificador):
        return any(
            elemento.identificador == identificador for elemento in elementos
        )

    def registrar_cliente(self, *datos):
        try:
            cliente = Cliente(*datos)
            if self._id_existe(self.clientes, cliente.identificador):
                raise ClienteInvalidoError(
                    f"Ya existe el cliente '{cliente.identificador}'."
                )
        except (ClienteInvalidoError, TypeError, ValueError) as error:
            logger.error("Registro de cliente fallido: %s", error)
            print(f"  [ERROR] {error}")
            return None
        else:
            self.clientes.append(cliente)
            logger.info("Cliente registrado: %s", cliente.describir())
            print(f"  [OK] {cliente.describir()}")
            return cliente
        finally:
            logger.info("Fin del intento de registro de cliente")

    def registrar_servicio(self, clase, *datos):
        try:
            if not isinstance(clase, type) or not issubclass(clase, Servicio):
                raise ServicioInvalidoError(
                    "La clase seleccionada no corresponde a un servicio."
                )
            servicio = clase(*datos)
            if self._id_existe(self.servicios, servicio.identificador):
                raise ServicioInvalidoError(
                    f"Ya existe el servicio '{servicio.identificador}'."
                )
        except (SoftwareFJError, TypeError, ValueError) as error:
            logger.error("Creación de servicio fallida: %s", error)
            print(f"  [ERROR] {error}")
            return None
        else:
            self.servicios.append(servicio)
            logger.info("Servicio creado: %s", servicio.describir())
            print(f"  [OK] {servicio.describir()}")
            return servicio
        finally:
            logger.info("Fin del intento de creación de servicio")

    def crear_reserva(self, identificador, cliente, servicio, duracion):
        try:
            reserva = Reserva(identificador, cliente, servicio, duracion)
            if self._id_existe(self.reservas, reserva.identificador):
                raise ReservaInvalidaError(
                    f"Ya existe la reserva '{reserva.identificador}'."
                )
            reserva.confirmar()
        except SoftwareFJError as error:
            logger.error("Reserva %s fallida: %s", identificador, error)
            print(f"  [ERROR] {error}")
            return None
        except (TypeError, ValueError) as error:
            logger.error("Datos incorrectos al crear reserva %s: %s", identificador, error)
            print(f"  [ERROR] {error}")
            return None
        else:
            self.reservas.append(reserva)
            logger.info("Reserva creada: %s", reserva.describir())
            print(f"  [OK] {reserva.describir()}")
            return reserva
        finally:
            logger.info("Fin del intento de reserva %s", identificador)


def simular():
    """Ejecuta trece operaciones de demostración del sistema."""
    gestor = GestorFJ()
    logger.info("=== INICIO DE LA SIMULACIÓN ===")

    print("\n=== SIMULACIÓN DE OPERACIONES ===")
    print("1. Cliente válido")
    c1 = gestor.registrar_cliente(
        "C1", "Laura Gómez", "1012345678", "laura@correo.com", "3101234567"
    )

    print("\n2. Cliente inválido (correo mal formado)")
    gestor.registrar_cliente(
        "C2", "Pedro Ruiz", "1098765432", "pedro-correo", "3109876543"
    )

    print("\n3. Cliente inválido (parámetros faltantes)")
    gestor.registrar_cliente("C3", "Ana")

    print("\n4. Servicio válido: sala")
    s1 = gestor.registrar_servicio(
        ReservaSala, "S1", "Sala Júpiter", 50000, 10
    )

    print("\n5. Servicio válido: equipo")
    s2 = gestor.registrar_servicio(
        AlquilerEquipo, "S2", "Portátil Pro", 8000, "Portátil"
    )

    print("\n6. Servicio válido: asesoría")
    s3 = gestor.registrar_servicio(
        AsesoriaEspecializada, "S3", "Asesoría en Python", 70000, "senior"
    )

    print("\n7. Servicio inválido (tarifa negativa)")
    gestor.registrar_servicio(
        ReservaSala, "S4", "Sala Marte", -100, 5
    )

    print("\n8. Reserva exitosa")
    r1 = gestor.crear_reserva("R1", c1, s1, 3) if c1 and s1 else None

    print("\n9. Reserva fallida (duración fuera de rango)")
    if c1 and s3:
        gestor.crear_reserva("R2", c1, s3, 10)

    print("\n10. Reserva fallida (servicio no disponible)")
    if c1 and s2:
        s2.disponible = False
        gestor.crear_reserva("R3", c1, s2, 5)

    print("\n11. Procesar reserva con impuesto y descuento")
    if r1:
        try:
            print(f"  [OK] Total: ${r1.procesar(0.19, 0.10):,.2f}")
        except SoftwareFJError as error:
            print(f"  [ERROR] {error}")

    print("\n12. Intentar procesar nuevamente la misma reserva")
    if r1:
        try:
            r1.procesar()
        except SoftwareFJError as error:
            print(f"  [ERROR] {error} | Causa: {error.__cause__}")

    print("\n13. Cálculo inconsistente (impuesto fuera de rango)")
    if s3:
        try:
            s3.calcular_costo(2, impuesto=5)
        except SoftwareFJError as error:
            logger.error("Cálculo inconsistente: %s", error)
            print(f"  [ERROR] {error}")

    logger.info("=== FIN DE LA SIMULACIÓN ===")
    print("\nLa aplicación siguió funcionando. Revise 'logs_software_fj.log'.")
    return gestor


def leer_texto(mensaje):
    """Solicita un texto no vacío."""
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        logger.warning("Entrada de texto vacía en el campo: %s", mensaje.strip())
        print("El valor no puede estar vacío.")


def leer_numero(mensaje, minimo=None, maximo=None, entero=False):
    """Solicita un número finito y valida su rango."""
    while True:
        try:
            entrada = input(mensaje).strip()
            valor = int(entrada) if entero else float(entrada)
            _validar_numero(valor, "El valor", minimo, maximo)
            return valor
        except (ValueError, OverflowError) as error:
            logger.warning(
                "Entrada numérica inválida en '%s': %s", mensaje.strip(), error
            )
            print(f"Entrada inválida: {error}")


def mostrar_clientes(gestor):
    print("\n--- CLIENTES REGISTRADOS ---")
    if not gestor.clientes:
        print("Todavía no hay clientes registrados.")
        return
    for cliente in gestor.clientes:
        print(
            f"{cliente.identificador} | {cliente.nombre} | "
            f"Documento: {cliente.documento} | {cliente.correo} | "
            f"Teléfono: {cliente.telefono}"
        )


def mostrar_servicios(gestor):
    print("\n--- SERVICIOS REGISTRADOS ---")
    if not gestor.servicios:
        print("Todavía no hay servicios registrados.")
        return
    for servicio in gestor.servicios:
        estado = "Disponible" if servicio.disponible else "No disponible"
        print(
            f"{servicio.identificador} | {servicio.describir()} | {estado}"
        )


def mostrar_reservas(gestor):
    print("\n--- RESERVAS REGISTRADAS ---")
    if not gestor.reservas:
        print("Todavía no hay reservas registradas.")
        return
    for reserva in gestor.reservas:
        print(f"{reserva.identificador} | {reserva.describir()}")


def buscar_por_id(elementos, identificador):
    """Busca una entidad por su identificador."""
    for elemento in elementos:
        if elemento.identificador == identificador:
            return elemento
    return None


def registrar_cliente_menu(gestor):
    print("\n--- REGISTRAR CLIENTE ---")
    datos = (
        leer_texto("Identificador: "),
        leer_texto("Nombre completo: "),
        leer_texto("Documento (6 a 12 dígitos): "),
        leer_texto("Correo electrónico: "),
        leer_texto("Teléfono (10 dígitos): "),
    )
    gestor.registrar_cliente(*datos)


def registrar_servicio_menu(gestor):
    print("\n--- REGISTRAR SERVICIO ---")
    print("1. Sala")
    print("2. Alquiler de equipo")
    print("3. Asesoría especializada")
    opcion = input("Seleccione el tipo de servicio: ").strip()

    clases = {
        "1": ReservaSala,
        "2": AlquilerEquipo,
        "3": AsesoriaEspecializada,
    }
    clase = clases.get(opcion)
    if clase is None:
        logger.warning("Tipo de servicio no válido seleccionado: %s", opcion)
        print("Opción no válida. No se registró el servicio.")
        return

    identificador = leer_texto("Identificador del servicio: ")
    nombre = leer_texto("Nombre del servicio: ")
    tarifa = leer_numero("Tarifa por hora ($): ", minimo=0.01)

    if clase is ReservaSala:
        capacidad = leer_numero(
            "Capacidad de la sala: ", minimo=1, entero=True
        )
        gestor.registrar_servicio(
            clase, identificador, nombre, tarifa, capacidad
        )
    elif clase is AlquilerEquipo:
        tipo = leer_texto("Tipo de equipo (portátil, proyector, etc.): ")
        gestor.registrar_servicio(
            clase, identificador, nombre, tarifa, tipo
        )
    else:
        print("Nivel: junior, senior o experto")
        nivel = leer_texto("Nivel del asesor: ").lower()
        gestor.registrar_servicio(
            clase, identificador, nombre, tarifa, nivel
        )


def crear_reserva_menu(gestor):
    print("\n--- CREAR RESERVA ---")
    if not gestor.clientes:
        logger.warning("Intento de crear reserva sin clientes registrados.")
        print("Primero debe registrar al menos un cliente.")
        return
    if not gestor.servicios:
        logger.warning("Intento de crear reserva sin servicios registrados.")
        print("Primero debe registrar al menos un servicio.")
        return

    mostrar_clientes(gestor)
    id_cliente = leer_texto("\nIdentificador del cliente: ")
    cliente = buscar_por_id(gestor.clientes, id_cliente)
    if cliente is None:
        logger.warning(
            "No se encontró el cliente solicitado al crear reserva: %s", id_cliente
        )
        print("No se encontró ese cliente.")
        return

    mostrar_servicios(gestor)
    id_servicio = leer_texto("\nIdentificador del servicio: ")
    servicio = buscar_por_id(gestor.servicios, id_servicio)
    if servicio is None:
        logger.warning(
            "No se encontró el servicio solicitado al crear reserva: %s", id_servicio
        )
        print("No se encontró ese servicio.")
        return

    identificador = leer_texto("Identificador de la reserva: ")
    duracion = leer_numero("Duración en horas (mínimo 1): ", minimo=1)
    gestor.crear_reserva(identificador, cliente, servicio, duracion)


def procesar_reserva_menu(gestor):
    print("\n--- PROCESAR RESERVA ---")
    mostrar_reservas(gestor)
    id_reserva = leer_texto("Identificador de la reserva: ")
    reserva = buscar_por_id(gestor.reservas, id_reserva)
    if reserva is None:
        logger.warning(
            "No se encontró la reserva solicitada para procesar: %s", id_reserva
        )
        print("No se encontró esa reserva.")
        return

    impuesto = leer_numero(
        "Impuesto (por ejemplo, 0.19 para 19 %): ", minimo=0, maximo=1
    )
    descuento = leer_numero(
        "Descuento (por ejemplo, 0.10 para 10 %): ", minimo=0, maximo=1
    )
    try:
        total = reserva.procesar(impuesto, descuento)
        print(f"\nReserva procesada correctamente. Total: ${total:,.2f}")
    except SoftwareFJError as error:
        print(f"\nNo se pudo procesar la reserva: {error}")


def cancelar_reserva_menu(gestor):
    print("\n--- CANCELAR RESERVA ---")
    mostrar_reservas(gestor)
    identificador = leer_texto("Identificador de la reserva: ")
    reserva = buscar_por_id(gestor.reservas, identificador)
    if reserva is None:
        logger.warning(
            "No se encontró la reserva solicitada para cancelar: %s",
            identificador,
        )
        print("No se encontró esa reserva.")
        return
    try:
        reserva.cancelar()
        print("La reserva fue cancelada correctamente.")
    except SoftwareFJError as error:
        logger.error("No se pudo cancelar la reserva %s: %s", identificador, error)
        print(f"No se pudo cancelar la reserva: {error}")


def cambiar_disponibilidad_menu(gestor):
    print("\n--- CAMBIAR DISPONIBILIDAD ---")
    mostrar_servicios(gestor)
    identificador = leer_texto("Identificador del servicio: ")
    servicio = buscar_por_id(gestor.servicios, identificador)
    if servicio is None:
        logger.warning(
            "No se encontró el servicio solicitado para cambiar disponibilidad: %s",
            identificador,
        )
        print("No se encontró ese servicio.")
        return
    servicio.disponible = not servicio.disponible
    estado = "disponible" if servicio.disponible else "no disponible"
    print(f"El servicio ahora está {estado}.")
    logger.info("Disponibilidad del servicio %s: %s", identificador, estado)


def menu_interactivo():
    """Punto principal de la interfaz de usuario por consola."""
    gestor = GestorFJ()
    logger.info("=== INICIO DEL SISTEMA INTERACTIVO ===")

    while True:
        try:
            print("\n" + "=" * 48)
            print("              SOFTWARE FJ")
            print("       Gestión de clientes y reservas")
            print("=" * 48)
            print("1. Registrar cliente")
            print("2. Registrar servicio")
            print("3. Mostrar clientes")
            print("4. Mostrar servicios")
            print("5. Crear reserva")
            print("6. Mostrar reservas")
            print("7. Procesar reserva")
            print("8. Cancelar reserva")
            print("9. Cambiar disponibilidad de un servicio")
            print("10. Ejecutar simulación de operaciones")
            print("0. Salir")
            print("-" * 48)

            opcion = input("Seleccione una opción: ").strip()

            if opcion == "1":
                registrar_cliente_menu(gestor)
            elif opcion == "2":
                registrar_servicio_menu(gestor)
            elif opcion == "3":
                mostrar_clientes(gestor)
            elif opcion == "4":
                mostrar_servicios(gestor)
            elif opcion == "5":
                crear_reserva_menu(gestor)
            elif opcion == "6":
                mostrar_reservas(gestor)
            elif opcion == "7":
                procesar_reserva_menu(gestor)
            elif opcion == "8":
                cancelar_reserva_menu(gestor)
            elif opcion == "9":
                cambiar_disponibilidad_menu(gestor)
            elif opcion == "10":
                simular()
            elif opcion == "0":
                print("\nGracias por utilizar Software FJ.")
                logger.info("=== CIERRE DEL SISTEMA INTERACTIVO ===")
                break
            else:
                logger.warning("Opción de menú no válida: %s", opcion)
                print("Opción no válida. Intente nuevamente.")

        except (KeyboardInterrupt, EOFError):
            print("\nCierre solicitado. Hasta pronto.")
            logger.info("Cierre del sistema solicitado por el usuario.")
            break
        except Exception as error:
            logger.exception("Error no previsto en el menú principal: %s", error)
            print(f"Se presentó un error inesperado: {error}")
            print("El sistema continuará funcionando.")


if __name__ == "__main__":
    menu_interactivo()

