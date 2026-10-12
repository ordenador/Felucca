# Planes de implementación

Generado con la skill improve el 11 de octubre de 2026, America/Santiago. Estos archivos son planes; no implementan funciones del firmware.

## Orden y estado

| Plan | Objetivo | Prioridad | Esfuerzo | Dependencias | Estado |
|---|---|---|---|---|---|
| [001](001-midi-nrpn-per-channel.md) | NRPN por canal, conservando CC y LEARN; definiciones Hapax | P1 | M | Ninguna | IN PROGRESS — software revisado y suite final PASS; aceptación física pendiente, sin flashear |

Estados: TODO, IN PROGRESS, DONE, BLOCKED con motivo, REJECTED con motivo. Solo marcar DONE después de los gates y la aceptación física definidos en el plan. Si la implementación y tests host pasan pero falta build real o Hapax/FM-1, conservar IN PROGRESS y registrar qué falta.

## Dependencias y límites

Primero baseline/mapa; luego selección/routing y regresión; después artefactos Hapax/build completo; finalmente prueba física coordinada con Mario. No hay permiso de flasheo, publicación, push ni PR en esta solicitud de planificación.

Base: ef1f561b6b105f20350f6b1eac0dc0789a357f00. Regla persistente: nunca crear/publicar ramas codex/; rama de implementación sugerida feat/midi-nrpn-per-channel. Conservar LOCAL-RUN.md y start-felucca.command.

Al planificar solo se comprobó sintaxis de tests/midi_control_test.c con cc -fsyntax-only. Faltan SDK y toolchain en rutas predeterminadas para build completo; no se ejecutó la suite ni se modificó código.

## Alternativas consideradas y excluidas de esta entrega

- Aumentar ML_N: mantiene asignaciones globales por número CC y altera persistencia; no resuelve el direccionamiento por canal.
- Resolver NRPN como índice P_* crudo: P_E0 se desplaza cuando crecen parámetros comunes; rompe archivos Hapax publicados.
- Datos NRPN14 bits: la mayoría de destinos tienen resolución nativa de7 bits; se empieza con DEPTH7 para reducir mensajes y alcance.
- Mezclar globales, operadores FM6 o Bank Select: requieren contratos y pruebas propios; quedan para planes posteriores.

## Auditoría cubierta

Parser/dispatch MIDI, RPN/CC/LEARN, routing, recovery, escritura/motion y harness/gates relevantes. No es una auditoría integral de seguridad, DSP, rendimiento físico ni de todos los firmwares del catálogo.

## Implementación autorizada — 11 de octubre de 2026

Mario autorizó implementar y ejecutar pruebas, sin flashear. Trabajo sin commits en rama feat/midi-nrpn-per-channel y worktree /Users/mfaundez/git/github/Felucca-worktrees/midi-nrpn-per-channel. El checkout principal conserva su código y archivos locales.

La implementación cubre 90 direcciones NRPN de 7 bits, estado por canal y USB/TRS, CC/LEARN/RPN/PC conservados y definiciones Hapax. Build real y suite final completa pasaron (exit 0); revisión de software terminada y omisiones documentadas. Sanitizers detectan dos shifts negativos preexistentes de ANALOG, reproducidos en el baseline original; no se modificó DSP.

Evidencia de implementación en el worktree: [001-nrpn-hapax.md](/Users/mfaundez/git/github/Felucca-worktrees/midi-nrpn-per-channel/plans/evidence/001-nrpn-hapax.md). La prueba física permanece pendiente por la instrucción expresa de no flashear.

## Publicación posterior a QA

Mario autorizó commit y push de esta implementación a su fork `ordenador/Felucca` en `feat/midi-nrpn-per-channel`, manteniendo la prohibición de flasheo. Los resultados de QA corresponden al snapshot identificado en la evidencia; las fuentes se comprobaron sin drift antes de publicar.

## Corrección ANALOG — 12 de octubre de 2026

Los shifts negativos detectados durante QA NRPN se corrigieron en
`fix/analog-ubsan-signed-shifts`, sobre `b3fdf11`. Gate estricto ANALOG y MIDI/NRPN
sin exclusiones, NOR estricto y suite de99 gates PASS;92 goldens sin cambios.
Objeto/ELF/app/loader/paquete target idénticos al baseline NRPN: cero delta de
RAM/pool/frames. Los resultados anteriores son evidencia histórica del código
previo al fix. [Informe y límites](evidence/002-analog-ubsan.md).

Mario autorizó commit y push de esta rama a su fork, sin flashear. La aceptación
física y el máximo absoluto de pila target siguen pendientes/no certificados.
