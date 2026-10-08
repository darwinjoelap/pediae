from django.db import models


class SolicitudIdempotente(models.Model):
    """
    Registro de cada envío de formulario hecho por offline.js.

    El navegador manda una clave única por formulario (_idem_key). Si la misma clave
    llega dos veces (doble toque, reintento por red lenta, cola offline), la segunda
    NO se vuelve a procesar: se responde con el mismo resultado de la primera.
    """
    PROCESANDO = 'procesando'
    OK = 'ok'
    ESTADOS = [(PROCESANDO, 'Procesando'), (OK, 'Completada')]

    clave = models.CharField(max_length=100, unique=True)
    usuario_id = models.IntegerField(null=True, blank=True)
    ruta = models.CharField(max_length=300)
    estado = models.CharField(max_length=12, choices=ESTADOS, default=PROCESANDO)
    location = models.CharField(max_length=500, blank=True)
    creado = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Solicitud idempotente'
        verbose_name_plural = 'Solicitudes idempotentes'

    def __str__(self):
        return f'{self.ruta} [{self.estado}]'
