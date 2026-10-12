# Plan 001: NRPN por canal para Felucca conservando CC y MIDI LEARN

> Instrucciones para quien implemente: lee el plan completo, conserva el comportamiento existente y ejecuta las verificaciones de cada etapa. Este documento autoriza planificación; no es una orden de flashear, publicar ni crear un PR.
>
> Comprobación de diferencias: desde /Users/mfaundez/git/github/Felucca ejecuta
> `git diff --stat ef1f561b6b105f20350f6b1eac0dc0789a357f00..HEAD -- firmware/src/core.h firmware/src/params.c firmware/src/midi_control.c firmware/src/seq.c tests/midi_control_test.c tests/ui_test.c tests/run_tests.sh`
> y `git diff -- firmware/src/core.h firmware/src/params.c firmware/src/midi_control.c firmware/src/seq.c tests/midi_control_test.c tests/ui_test.c tests/run_tests.sh`.
> Si cambió código relevante, revisa los extractos antes de implementar y actualiza el plan cuando sus supuestos ya no se cumplan.

## Estado y objetivo

- Estado: TODO; únicamente planificado.
- Prioridad P1; esfuerzo M; riesgo MED; categoría feature.
- Fecha: 11 de octubre de 2026, America/Santiago.
- Base: ef1f561b6b105f20350f6b1eac0dc0789a357f00, v1.5.1-1-gef1f561.
- Repositorio: /Users/mfaundez/git/github/Felucca.
- Origin: https://github.com/ordenador/Felucca.git.
- Upstream: https://github.com/hugelton/Felucca.git.
- Rama al planificar: main; HEAD igual a upstream/main.
- Dependencias de otros planes: ninguna.
- No hay cambios tracked. Conservar LOCAL-RUN.md y start-felucca.command, ambos untracked.

Mario tiene dos M-VAVE FM-1 y utiliza Squarp Hapax como secuenciador y controlador. Quiere automatizar parámetros de Felucca sin consumir las 16 asignaciones MIDI LEARN globales. El mismo NRPN debe controlar un parámetro de la pista resuelta por el canal: CH1→T1, CH2→T2, etc.; el segundo equipo puede usar CH5–8. Los CC fijos, los CC aprendidos, expresión, RPN0 de bend, sustain, PC y transporte conservarán sus funciones.

Resultado mínimo: **90 direcciones estables**, 82 parámetros comunes y ocho posiciones del motor actual. Un NRPN no consume ningún slot LEARN. No hay un límite de 16 asignaciones NRPN; sí siguen existiendo límites de lanes de Hapax, ancho de banda y capacidad de DSP.

## Decisiones de protocolo

1. Dirección NRPN de 14 bits: `(MSB << 7) | LSB`.
2. **Valor de 7 bits, 0–127, en CC6.** Hapax admite DEPTH=7. Esto amplía la cantidad de destinos, no la resolución del DSP. CC38 permanece operativo para RPN0; con NRPN se ignora. No anunciar compatibilidad con DEPTH=14 en esta versión.
3. MSB=0: parámetros comunes, con LSB literal y estable según la tabla de este plan. MSB=1: LSB0–7→P_E0–P_E7 del motor actual. MSB2–126, LSB no registrados y 127:127 no escriben parámetros.
4. El registro de direcciones debe referenciar símbolos P_* por nombre. No resolver MSB0 mediante `id = LSB`, ni asignar direcciones a través del orden de una lista filtrada. Los números de la tabla son una API que queda congelada; no reutilizar huecos retirados.
5. Reutilizar **midi_cc_set(t,id,value)** después de validar dirección e id. La escala es exactamente la existente:
   `min + floor((value*(max-min)+63)/127)`.
   P_PAN: 0→−64, 64→0, 127→63. Enums: cuantización por esa fórmula, no índices directos. ENV SYNC mantiene valores almacenados 0–127 repartidos sobre sus 25 tiempos musicales, como ya hace Felucca.
6. El destino se resuelve con `midi_track(ch)` **al recibir CC6**. En bloque de canales no depende de song.sel. SEL mantiene la semántica actual: canal admitido→pista seleccionada al recibir el dato.
7. Selección NRPN independiente por **entrada USB/TRS y canal**, en 32 estados pequeños. Evita completar una selección USB con bytes TRS. Los parámetros de la pista siguen compartidos: si ambas entradas controlan el mismo destino, el último dato válido gana.
8. RPN de bend conserva su estado compartido por canal, como actualmente. Recibir CC99/98 sigue cancelando RPN. Recibir CC101/100 cancela NRPN de ambas entradas en ese canal. No extender ni rediseñar RPN0.
9. CC y NRPN pueden cambiar el mismo parámetro; prevalece el último dato válido. NRPN no pasa por midi_learned ni cambia ml_arm/ml_heard. Aprender CC74 sigue reemplazando su función fija, como ahora.
10. Sin persistencia nueva: las selecciones NRPN son estado volátil, no datos de proyecto/settings. Los valores de parámetros se guardan por los mecanismos existentes, sin cambiar formatos ni incrementar escrituras flash por cada mensaje.

### Ejemplos completos

En CH1, índice de parámetro de ANALOG CUT:
~~~
CC99=1
CC98=4
CC6=96
~~~
En CH2, con FM6, índice MLVL:
~~~
CC99=1
CC98=2
CC6=64
~~~
En ese segundo ejemplo MLVL queda en cero. Un mensaje CC74 previo/siguiente sigue produciendo su efecto actual, salvo una asignación LEARN que lo reemplace.

Cierre de selección compatible:
~~~
CC101=127
CC100=127
~~~
Este RPN Null cancela NRPN de ambas entradas para ese canal, sin modificar sonido ni rango de bend.

Definición Hapax propuesta:
~~~
[NRPN]
0:9:7 LFO Rate
0:39:7 Panorama
0:96:7 Insert Tipo
1:4:7 Motor E5
[/NRPN]
~~~
Se nombran destinos; no crear 90 lanes automáticamente. Las nuevas definiciones conservarán CC, usarán VERSION 1 y no enviarán valores DEFAULT al cargar. Referencia oficial: https://squarp.net/hapax/instr_def/template.txt.

## Qué cubre y qué no

Incluye mixer/nivel/pan/mute, ADSR y cantidades ENV, LFO, arp, escala/transposición, controles del secuenciador de pista, DIST/INSERT/SLICER/envíos, matriz, SPREAD, filtro ANALOG, ENV SYNC, niveles de lanes DRUM y ocho parámetros de motor.

La disponibilidad sonora sigue dependiendo del motor/modo: ADSR común no modifica FM6; los niveles de lanes son de DRUM; P_FTYPE es ANALOG; E1–E8 tienen nombres distintos según motor. Exponer un parámetro no hace que un motor use algo que actualmente ignora.

Quedan fuera de esta versión:
- Bytes individuales de operadores FM6, su patch completo y protocolo Yamaha/SysEx.
- Globales G_*: tempo, ruta MIDI, motor, modelo/tamaño de reverb, parámetros globales de delay/chorus, proyectos y acciones de guardar/cargar.
- Bank Select, cambios de PC, increment/decrement CC96/97 y valores NRPN de 14 bits.
- Suavizado nuevo, nuevos LFO/motores, cambios del secuenciador y del presupuesto de voces.
- Una página de configuración NRPN o toggle: el nuevo protocolo es aditivo y responde únicamente después de una selección válida.
- Cambios en el editor web, instalador, HAL, USB descriptors, UART parser, OTA, formatos de persistencia o audio DSP.

Hapax permite 64 lanes de automatización por pista. Su manual indica que **no graba NRPN entrante**; este plan permite emitir curvas NRPN preparadas en Hapax, no capturar como NRPN los giros del panel. No se agrega MIDI OUT de parámetros. Fuente: https://squarp.net/hapax/manual/modeautomation/.

## Estado actual y puntos de integración

Felucca es C de firmware embebido con fuentes incluidas en una unidad de traducción. No introducir un proyecto aparte ni un framework. Mantener funciones static, tipos enteros, convenciones de comentarios en inglés, SPDX GPL-3.0-only en fuentes nuevas y arrays constantes; sin heap ni operaciones de E/S en el handler.

| Archivo y línea de base | Función y hecho |
|---|---|
| firmware/src/core.h:44 | P_* de pista, P_E0=103/P_COUNT=111; los comunes nuevos se añaden antes de P_E0 |
| firmware/src/params.c:81 | TP[] define límites; eng_*.c define los ocho parámetros de motor |
| firmware/src/params.c:239 | param_desc_of() usado por CC; no requiere nuevas tablas de escalas |
| firmware/src/midi_control.c:10 | midi_channel_t y midi_ch[16], bend/RPN compartidos por canal |
| firmware/src/midi_control.c:215 | MIDI_CC_MAP y MIDI_CC_ENG actuales |
| firmware/src/midi_control.c:229 | midi_cc_set() escribe t->p y motion_capture si cambió el valor |
| firmware/src/midi_control.c:258 | CC6/38/98–101 no son aprendibles |
| firmware/src/midi_control.c:304 | midi_control() gestiona RPN0; hoy CC99/98 solo lo cancelan |
| firmware/src/midi_control.c:367 | midi_route_block() libera/resetea canales fuera del bloque |
| firmware/src/midi_control.c:394 | midi_event() filtra fuera del bloque antes de toda escritura |
| firmware/src/seq.c:1115 | midi_in_block/midi_track; incluye midi_control.c |
| firmware/src/seq.c:1234 | detecta cambio de ROUT; aquí invalidar todas las selecciones NRPN |
| firmware/src/seq.c:1241 | overflow vacía stream y midi_ch; añadir reset del nuevo estado NRPN |
| firmware/src/seq.c:1278 | drena cola; ya conoce source=1 USB / 2 TRS, pero no lo pasa a midi_event |
| firmware/src/usb.c:169 | cola MQ=64; conserva source; no hay que modificar el productor |
| tests/midi_control_test.c:7 | reset del test; queued() usa cola real y source |
| tests/midi_control_test.c:28 | pruebas RPN/bend/expresión existentes |
| tests/midi_control_test.c:357 | caracterización de todos los CC fijos y motion |
| tests/midi_control_test.c:430 | pruebas LEARN, prioridades y límites |
| tests/midi_control_test.c:592 | pruebas PC; deben conservarse |
| tests/ui_test.c:214 | power-on simulado reinicia midi_ch; añadir reset del estado NRPN |
| tests/run_tests.sh:245 | comando de compilación e integración MIDI |
| CONTRIBUTING.md | exige suite y prueba en un FM-1 real para cambios destinados a contribuir |

Extractos para comprobación:
~~~
static int midi_in_block(uint32_t ch)
{
    int32_t b = midi_base();
    return b >= 0 && ch - (uint32_t)b < NPART;
}
static track_t *midi_track(uint32_t ch) { return midi_in_block(ch) ? &trk[ch - (uint32_t)midi_base()] : TSEL; }
~~~
~~~
const param_desc_t *d = param_desc_of(eng_idx(t->eng_req), id);
int32_t v = d->min + ((int32_t)value * (d->max - d->min) + 63) / 127;
if (d->max <= d->min || t->p[id] == v)
    return;
t->p[id] = (int16_t)v;
(void)motion_capture(t, id, (int16_t)v);
~~~
~~~
case 101: c->rpn_msb = (uint8_t)value; break;
case 100: c->rpn_lsb = (uint8_t)value; break;
case 99: case 98:
    c->rpn_msb = c->rpn_lsb = 127;
    break;
~~~

## Registro NRPN v1 obligatorio

MSB0, **82 entradas**. La relación coincide con IDs actuales solo al arrancar; el registro explícito conservará direcciones aunque cambie el enum interno.

| MSB:LSB | Símbolo destino |
|---|---|
| 0:0 | P_LEVEL |
| 0:1 | P_ATK |
| 0:2 | P_DEC |
| 0:3 | P_SUS |
| 0:4 | P_REL |
| 0:5 | P_ED_FLT |
| 0:6 | P_ED_PIT |
| 0:7 | P_ED_SHP |
| 0:9 | P_LRATE |
| 0:10 | P_LWAVE |
| 0:11 | P_LPHASE |
| 0:12 | P_LFADE |
| 0:13 | P_LD_PIT |
| 0:14 | P_LD_FLT |
| 0:15 | P_LD_SHP |
| 0:16 | P_LD_AMP |
| 0:17 | P_AMODE |
| 0:18 | P_ARATE |
| 0:19 | P_AOCT |
| 0:20 | P_AGATE |
| 0:21 | P_ASWING |
| 0:22 | P_APROB |
| 0:23 | P_AHOLD |
| 0:24 | P_AORDER |
| 0:25 | P_ROOT |
| 0:26 | P_SCALE |
| 0:27 | P_QUANT |
| 0:28 | P_TRANS |
| 0:29 | P_SLEN |
| 0:30 | P_SDIV |
| 0:31 | P_SSWING |
| 0:32 | P_SGATE |
| 0:33 | P_DIST |
| 0:34 | P_CHOR |
| 0:35 | P_DLY |
| 0:36 | P_REV |
| 0:37 | P_VOICE |
| 0:38 | P_GLIDE |
| 0:39 | P_PAN |
| 0:40 | P_MUTE |
| 0:41 | P_GLMODE |
| 0:42 | P_PRIO |
| 0:43 | P_ALLOC |
| 0:44 | P_DETUNE |
| 0:45 | P_SLCR |
| 0:46 | P_SLPAT |
| 0:47 | P_SLRATE |
| 0:48 | P_SLDEPTH |
| 0:49 | P_M1SRC |
| 0:50 | P_M1DST |
| 0:51 | P_M1AMT |
| 0:52 | P_M2SRC |
| 0:53 | P_M2DST |
| 0:54 | P_M2AMT |
| 0:55 | P_M3SRC |
| 0:56 | P_M3DST |
| 0:57 | P_M3AMT |
| 0:58 | P_M4SRC |
| 0:59 | P_M4DST |
| 0:60 | P_M4AMT |
| 0:81 | P_CHRD |
| 0:82 | P_VOIC |
| 0:83 | P_LN0 |
| 0:84 | P_LN1 |
| 0:85 | P_LN2 |
| 0:86 | P_LN3 |
| 0:87 | P_LN4 |
| 0:88 | P_LN5 |
| 0:89 | P_LN6 |
| 0:90 | P_LN7 |
| 0:91 | P_LSYNC |
| 0:92 | P_LTRIG |
| 0:93 | P_LPOL |
| 0:94 | P_SQNT |
| 0:95 | P_SPRD |
| 0:96 | P_ITYPE |
| 0:97 | P_IA |
| 0:98 | P_IB |
| 0:99 | P_IC |
| 0:100 | P_IMIX |
| 0:101 | P_FTYPE |
| 0:102 | P_ESYNC |

MSB1, **ocho entradas**:

| MSB:LSB | Símbolo destino |
|---|---|
| 1:0 | P_E0 |
| 1:1 | P_E1 |
| 1:2 | P_E2 |
| 1:3 | P_E3 |
| 1:4 | P_E4 |
| 1:5 | P_E5 |
| 1:6 | P_E6 |
| 1:7 | P_E7 |

Reservar sin asignar 0:8 (P_ED_FX inerte), 0:61–80 (DIGITAL legacy, incluso si se compila FELUCCA_FM4=1), 0:103–127 y 1:8–127. Los futuros parámetros se asignan explícitamente en huecos reservados de extensión sin mover ninguna dirección publicada. 127:127 se trata como NRPN Null. Si el espacio común MSB0 se agota, abrir una nueva página distinta de MSB1.

## Archivos permitidos al implementar

Modificar:
- firmware/src/midi_control.c.
- firmware/src/seq.c, solo paso de source y resets de selección.
- tests/midi_control_test.c, sin reemplazar ni eliminar cobertura actual.
- tests/ui_test.c, solo reset del estado nuevo en power-on simulado.
- tests/run_tests.sh, solo comprobaciones nuevas del generador/artefactos NRPN.
- README.md, breve apartado NRPN y enlace a documentación.
- plans/README.md, estado del plan.

Crear:
- firmware/src/midi_nrpn_map.h: registro único de direcciones comunes y E1–E8, nombres ASCII y símbolos; incluido por midi_control.c.
- tools/gen_hapax_nrpn.py: generador determinista con stdlib Python y modo --check.
- tests/hapax_nrpn_test.py: validación estructural y de correspondencia de definiciones.
- docs/midi-nrpn.md: protocolo, tabla, rangos, ejemplos, CC conservados y límites.
- docs/hapax/felucca-nrpn-poly.txt: TYPE POLY, OUTPORT/OUTCHAN NULL, nombres comunes/E1–E8 genéricos y CC actuales.
- docs/hapax/felucca-nrpn-drum.txt: TYPE DRUM, OUTPORT NULL, OUTCHAN4, ocho lanes canónicas en CH4 y CC aplicables.
- plans/evidence/001-nrpn-hapax.md: evidencia de pruebas/pendientes, versiones, comandos, memoria y resultados.

No modificar core.h/params.c/eng_*.c ni el mapa P_* para acomodar NRPN. No modificar SLOOP ni /Users/mfaundez/git/github/ordenador/hapax-*.txt de la revisión anterior. Los archivos nuevos se distinguen por nrpn; no presentan NRPN como una capacidad de la release original v1.5.1.

## Git y publicación

No se crea rama durante la planificación. Para implementación autorizada, rama sugerida **feat/midi-nrpn-per-channel**. Nunca usar nombres codex/; comprobar la rama antes de crear worktree, push o PR y transmitir esta preferencia a agentes delegados.

No commits, push ni PR por este plan. Cuando Mario solicite implementación, conservar su trabajo existente; si posteriormente pide commits, usar mensajes descriptivos acordes con el repo. Una prueba host no autoriza instalar firmware: la prueba física se coordina como una etapa aparte.

## Comandos y prerrequisitos

Desde la raíz del repo:

| Propósito | Comando | Éxito esperado |
|---|---|---|
| Sintaxis de la integración existente | cc -O1 -w -fsyntax-only -Ibuild/gen -Ifirmware/src tests/midi_control_test.c | exit 0; verificado en esta planificación |
| Preparar salida de pruebas, durante implementación | mkdir -p build/host | exit 0, solo directorio ignorado |
| Compilar integración MIDI | cc -O1 -Wall -Wno-unused-function -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test tests/midi_control_test.c -lm | exit 0 |
| Ejecutar integración MIDI | build/host/midi_control_test | exit 0 y MIDI control/clock integration tests passed |
| Compilar ASan/UBSan | cc -O1 -w -g -fsanitize=address,undefined -fno-omit-frame-pointer -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test_asan tests/midi_control_test.c -lm | exit 0 |
| Ejecutar ASan/UBSan | ASAN_OPTIONS=detect_leaks=0 build/host/midi_control_test_asan | exit 0, sin diagnósticos sanitizer |
| Comprobar generación, herramienta por crear | python3 tools/gen_hapax_nrpn.py --check | exit 0, archivos coinciden con registro; ninguna escritura |
| Validar definiciones, prueba por crear | python3 tests/hapax_nrpn_test.py | exit 0, CC/NRPN/lanes válidos y mapas coincidentes |
| Build de firmware | ./build.sh | exit 0, build/felucca.fwsc, build/felucca.dis y loader |
| Regresión completa | sh tests/run_tests.sh | exit 0, sin regenerar goldens ni budgets |
| Espacios en diff | git diff --check | exit 0 |
| Alcance | git status --short | solo archivos permitidos y untracked preexistentes |

Al planificar existen build/gen/felucca_tables.h y felucca_samples.h; la comprobación de sintaxis pasó. No existe build/host ni el paquete/disassembly completo. cc, Python, Node y Docker están instalados. No se encontró toolchain JieLi ni SDK en sus rutas predeterminadas; JIELI_TOOLCHAIN y AC79_SDK no están definidos. No se ejecutó un build ni la suite, ni se instalaron dependencias.

Para build completo localizar instalaciones existentes o provisionar los prerrequisitos de BUILDING.md: toolchain pi32v2, SDK AC79, Pillow/fontTools y Docker disponible en macOS. No cambiar variables HOME/home/CODEX_HOME. No sustituir el build real por artefactos heredados ni inventar rutas. Los comandos propuestos para herramientas nuevas se convierten en gates ejecutables cuando esas herramientas existan.

## Etapas de implementación

### 1. Establecer baseline y registro

Compilar y ejecutar el MIDI test original, guardando resultado/commit en plans/evidence/001-nrpn-hapax.md. Crear el registro único con 82 entradas comunes explícitas y ocho entradas de motor. Una macro X(address, P_SYMBOL, ASCII_NAME), o estructura equivalente, debe permitir que C resuelva símbolos y Python extraiga direcciones/nombres sin una segunda tabla manual. No compilar strings de nombres dentro del firmware si no se usan.

Usar tabla constante MSB0 con cero=sin destino y valores id+1, o un switch explícito. No usar cero como sentinel del parámetro porque P_LEVEL=0 es válido. Para motor resolver P_E0+k únicamente con MSB1/LSB<8. Validar id<P_COUNT antes de leer descriptor o t->p.

**Verificación:** baseline MIDI exit 0; prueba de registro comprueba 82+8 entradas, 90 direcciones únicas, 0:0→P_LEVEL, 0:39→P_PAN, 1:4→P_E4 y ningún hueco retirado asignado. No avanzar con un baseline que ya falla sin documentar y resolver la causa.

### 2. Añadir selección NRPN y conservar RPN

Añadir estado compacto {msb, lsb, seen} para [2][16]. seen=0 es sin selección; bits MSB/LSB indican qué componentes se recibieron. Cero de dirección/valor es un dato válido. No añadir ese estado a structs persistidos ni aumentar ML_N.

Comportamiento:
- Primera CC99/98 tras reset: invalidar RPN del canal como antes y almacenar/markear solo su componente en el estado de source.
- Selección completa solo con seen=3. Aceptar MSB→LSB y LSB→MSB.
- Mientras se mantiene esa selección, admitir CC6 repetidos y cambios de solo un componente, preservando el otro; no exigir que selección/datos sean adyacentes.
- Un número desconocido completo reemplaza el anterior; CC6 no hace nada. No volver al último NRPN conocido ni alterar bend.
- 127:127 invalida selección de esa entrada/canal.
- CC101/100 conserva la selección RPN actual según código existente y limpia NRPN en ambas entradas de ese canal, incluso si es RPN desconocido o Null.
- CC6: RPN0 primero, ruta existente y clamping existente; en caso contrario, aplicar NRPN válido de la entrada actual a midi_track(ch). CC38: solo cents de RPN0, ignorado para NRPN.
- CC96/97 permanecen ignorados.

Pasar source desde events_block a una nueva función midi_event_source(st,ch,d1,d2,source), conservando un wrapper midi_event con cuatro argumentos para tests/llamadas existentes, delegado a USB=1. Añadir source a midi_control o crear midi_control_source. No introducir un global mutable “último source”. Preservar el filtro de canales como primera acción de dispatch y la llamada mod_midi existente. Antes de indexar el estado selector, validar source=1 o 2; un source desconocido ignora selección/datos NRPN sin cambiar el comportamiento de otros mensajes. No usar source-1 sin validación. Los eventos normales ya traen ch0–15 y data0–127 del parser; los helpers nuevos no deben aceptar un id fuera del registro.

**Verificación:** MIDI integration exit 0 con casos nuevos para selección parcial, inversión de orden, repetición, unknown, RPN/NRPN alternados y Null; controles/bend originales siguen pasando. Confirmar que USB CC99 + TRS CC98 nunca produce una escritura.

### 3. Completar routing, resets y escritura de parámetros

Para NRPN conocido usar midi_cc_set, evitando UI/flash y conservando motion_capture. No aplicar param_fit a valores live: esa función tiene semántica de persistencia y convierte slots de banco FM6 a OWN; no es el setter de CC.

Agregar helpers de reset por canal y de todos los estados:
- Inicialización BSS y power-on simulado de tests.
- CC121: reset de selección en ambas entradas de ese canal, conservar parámetros y sensibilidad bend.
- Cualquier cambio G_ROUTE detectado en events_block: limpiar todas las selecciones NRPN, incluyendo cambio hacia SEL, sin ampliar el reset de RPN/bend existente.
- Overflow/pérdida de stream en events_block: limpiar todas las selecciones.
- midi_route_block: asegurar que los canales descartados no conservan selección; un reset adicional de NRPN aquí puede ser redundante pero debe ser coherente.

En SEL, cambiar song.sel entre selección y CC6 controla la seleccionada al recibir el dato. Los PC conservan selección NRPN y E1–E8 siguen el motor actual; documentar que sus etiquetas pueden cambiar tras cargar o editar un motor. Fuera del bloque ningún byte modifica ni selecciona nada.

**Verificación:** tests USB y TRS para cuatro pistas y los cuatro bloques; cambio de ruta/overflow/CC121 exige nueva selección completa; CC120/123 conserva su semántica; CC121 de CH1 no invalida NRPN de CH2; LEARN lleno y armado no captura ni bloquea NRPN. ASan/UBSan exit 0.

### 4. Documentar y generar definiciones Hapax

Generador sin dependencias externas, red ni instalación. Leer registro único, emitir archivos UTF-8 deterministas y validar números/nombres. --check compara en memoria y termina con exit 1 si hay diferencias; nunca escribe. Modo normal solo escribe docs/hapax/felucca-nrpn-poly.txt y felucca-nrpn-drum.txt.

Ambos incluyen las 90 direcciones sin duplicados. Los nombres comunes serán legibles y diferenciados: LFO Rate, ENV Pitch, LFO Pitch, Matrix1 Src/Dst/Amount, etc. E1–E8 genéricos como Motor E1…Motor E8; docs explica nombres para ANALOG/FM6 y cómo renombrarlos en Hapax. P_LN0…7 llevarán nombres de pieza DRUM. No inventar una asignación LEARN para obtener esos destinos.

POLY OUTCHAN NULL; DRUM OUTCHAN4 y lanes CH4:
36 Bombo, 38 Caja, 39 Palmas, 42 Hat cerrado, 46 Hat abierto, 45 Tom, 37 Aro, 56 Campana. Cada lane ROW:NULL:4:NOTE. Usar OUTPORT/INPORT/INCHAN/MAXRATE NULL. Para segundo equipo CH5–8, documentar cambio de OUTCHAN y de todos los canales explícitos de lanes a 8.

Conservar la capacidad CC en archivos:
- POLY: 1/5/6/7/10/11/38/64/71/72/73/74/75/91/93/94/98/99/100/101/120/121/123 con nombres actuales y condiciones.
- DRUM: 1/7/10/11/74/91/93/94/120/121/123.
- CC98/99 ahora son selección NRPN, no rotularlos únicamente “Cancelar RPN”.
- No defaults, ASSIGN ni lanes AUTOMATION creados de oficio.
- [PC] POLY: 1 Primer sonido motor; DRUM 1 STD, 2 80, 3 10, 4 66, 5 55, 6 77. Son etiquetas, no nuevos mensajes PC/Bank Select.
- [NRPN] usa MSB:LSB:7. NRPN es independiente de los CC nombrados.

Documentar que banco es dirección, **no MIDI Bank Select**; que 7 bits significan resolución nativa actual; ENV SYNC, enums y motores tienen escalas propias; y que los archivos requieren este fork modificado. Adjuntar secuencias de bytes/CC reproducibles y recomendación de configurar lanes manualmente.

**Verificación:** python3 tools/gen_hapax_nrpn.py --check y python3 tests/hapax_nrpn_test.py exit 0. Test Python comprueba 90 nombres NRPN únicos por archivo, DEPTH7, chars ASCII permitidos, canal/notas reales, presencia de CC actuales y ausencia de DEFAULT/auto-lanes; fallos deliberados de duplicados o cambio de dirección deben detectarse. Registrar estas pruebas en tests/run_tests.sh sin reorganizar la suite.

### 5. Regresión completa y coste

Ejecutar build real y tests/run_tests.sh cuando estén disponibles toolchain/SDK. Repetir las verificaciones host con FELUCCA_SLICE=0 y FELUCCA_FM4=1 mediante -D en el comando del MIDI test: los NRPN comunes/E1–E8 conservan dirección y DIGITAL legacy sigue sin exponerse.

Guardar tamaño de paquete, memoria estática y diferencias del binario/disassembly. Estado selector esperado: 96 bytes si son tres uint8 por cada una de 32 selecciones; map común uint16 de 128 entradas: 256 bytes de constantes. Reportar tamaños reales. No modificar memoria de motor ni tablas de DSP. Límite de RAM adicional para este cambio: ≤256 bytes de estado estático; si se excede, investigar antes de ampliar.

Prueba de estrés host: 10.000 cambios válidos intercalados en cuatro canales con note-on/off, sustain, bend, clock y CC existentes; alimentar por grupos que drene el firmware. Deben coincidir valores finales esperados, no quedar voces colgadas ni owners inconsistentes. Prueba separada de saturación: provocar overflow intencionado y comprobar recuperación e invalidación de selección, sin exigir que una cola finita conserve eventos descartados.

**Verificación:** build/suite exit 0, goldens y budgets actuales sin cambios, git diff --check exit 0, ASan/UBSan sin errores. Si faltan herramientas de build completo, registrar “host verificado; build/hardware pendiente”; no marcar la implementación como aceptada en hardware.

### 6. Aceptación con Hapax y dos equipos

Etapa física posterior, coordinada con Mario; no instalar automáticamente por haber creado este plan. Antes de una prueba autorizada guardar backup de datos, identificar unidades y versión/commit del paquete, y conservar un paquete para restaurar.

1. Cargar las definiciones y verificar que aparecen los 90 destinos nombrados. En una pista Hapax crear dos lanes NRPN y una CC; cambiar OUTCHAN y confirmar destino por canal, sin cambiar selección del panel FM-1.
2. A con CH1–4 y B con CH5–8: emitir 1:4 por CH1 y CH5 y verificar que cambia E5 exclusivamente de T1 del equipo correspondiente. Repetir cuatro pistas y NRPN comunes; PC/CC/sustain/bend siguen como antes.
3. FM6 en CH2: 1:2/1:3/1:4 controlan MLVL/MRAT/MEG; no confundirlos con operadores individuales. ANALOG en CH1: 1:4 CUT, 1:5 RES y 0:101 TYPE.
4. USB y DIN→TRS por separado. En batería confirmar canales explícitos de lanes; OUTCHAN controla automatización, no reemplaza el canal explícito de las notas.
5. A 120 BPM, comenzar con 4 lanes NRPN a MAX RATE 8 ppqn (hasta 16 actualizaciones/s por lane), luego 8 lanes distribuidas por pistas, más notas/clock/CC. Medir la salida efectiva; reportar carga, pérdidas, latencia observable y cualquier zipper noise.
6. Referencia DIN sin running status: una selección completa + valor ocupa tres CC, nueve bytes, ~2.88 ms a 31.250 bps. Ocho lanes a 16 cambios/s implican hasta 1.152 bytes/s, antes de clock/notas; no asumir que Hapax reenvía siempre selección ni que siempre la omite. Capturar mensajes reales cuando sea posible.
7. Mantener la prueba diez minutos, terminar notas/pedal y comprobar ausencia de voces colgadas. Con pérdida intencionada de datos, la recuperación debe exigir nueva selección. Documentar límites medidos en vez de prometer automatización ilimitada.

Registrar firmware/commit, versión Hapax, entrada/puerto, canales, motores, lanes/rate, pasos exactos, captura MIDI cuando exista, resultados y restauración en plans/evidence/001-nrpn-hapax.md.

## Matriz mínima de tests automatizados

Los grupos nuevos pueden añadirse como nrpn_*_test() a tests/midi_control_test.c usando queued(), events_block(), um_byte() y midi_test_reset() reales; no probar únicamente helpers aislados.

| Grupo | Casos requeridos |
|---|---|
| Selección | power-on/CC6 solo sin efecto; MSB o LSB solo sin efecto; ambos órdenes; selección0:0 válida; CC6=0 válido; CC6 repetidos; componente reutilizado |
| Dirección | 90 direcciones; 0:8/61–80/103–127 y 1:8–127 ignorados; MSB2,126,127 desconocidos; 127:127 Null; ningún acceso fuera de array |
| Escala | cada entrada común con valores0/64/127; P_PAN=−64/0/63; enums, bipolar matrix, ADSR/ENV SYNC; motor E1–E8 de ANALOG y FM6 según descriptor |
| Routing | cuatro pistas; bloques1–4/5–8/9–12/13–16; canal externo descarta selección y datos; SEL controla seleccionada al CC6; cambiar panel no retargetea modo bloque |
| Entrada | USB completo y TRS real con running status y realtime intercalado; mezclar selectores de dos fuentes no completa selección; dos selecciones completas simultáneas por fuente; source desconocido no accede fuera del array ni escribe NRPN |
| RPN | NRPN cancela RPN; RPN cancela ambas selecciones NRPN del canal; RPN0 conserva semis/cents, clamping y bend; unknown RPN no modifica sonido; RPN Null bloquea CC6 posterior |
| Compatibilidad | todos los tests CC/PC/sustain/AT/wheel/panic existentes; CC y NRPN al mismo destino último gana; LEARN fijo reemplaza CC pero no NRPN; NRPN no ocupa slots ni consume captura LEARN |
| Reset | CC121 solo canal afectado; cambio de ROUT en ambos sentidos; overflow; power-on simulado; sin cambios de parámetros/LEARN guardados por solo seleccionar/resetear |
| Motion | NRPN dispara motion_capture igual a CC; REC off sin registro; REC on/playing seleccionado registra; otro track sigue regla actual; valor repetido no crea nuevo registro; no cambiar límite interno128 |
| Config/build | default, SLICE=0 y FM4=1; ASan/UBSan; 10.000 cambios distribuidos; overflow recupera; lectura/guardado de settings y proyectos existentes mediante suite |

Para convertir resolución a valor esperado en tests, calcular con descriptor y fórmula independiente, y añadir anclas numéricas explícitas. No depender solamente del registro de producción para afirmar que sus direcciones son correctas: congelar las expectativas publicadas de 0:0/0:39/0:96/0:102/1:0/1:4/1:7 y exclusiones.

## Criterios de finalización

- [ ] 90 direcciones estables, ninguna depende del desplazamiento de P_E0.
- [ ] CC/LEARN/RPN0/PC/expresión/transporte anteriores pasan sin cambios de comportamiento.
- [ ] NRPN por canal y selección por entrada verificados en USB/TRS y en todos los bloques.
- [ ] Null, unknown, datos parciales, resets y overflow no escriben un parámetro equivocado.
- [ ] NRPN no consume slots LEARN ni provoca escritura flash directa.
- [ ] Generación determinista --check y tests de definiciones pasan.
- [ ] ASan/UBSan, build real y suite pasan; no cambiar goldens ni budgets.
- [ ] Diff acotado a lista permitida; untracked del usuario intactos; ninguna rama codex/.
- [ ] Prueba Hapax/FM-1 real registrada para aceptación física; si falta, estado IN PROGRESS con pendiente explícito.
- [ ] plans/README.md actualizado con estado y enlace a evidencia.

## Condiciones para detenerse o revisar el plan

- Extractos/mapa o semántica de RPN/routing cambian respecto de la base; no adaptar números publicados por intuición.
- Se requiere editar persistencia/core/engines/DSP/editor/HAL/OTA u otro archivo fuera del alcance.
- La implementación hace pasar pruebas eliminando verificaciones CC/RPN o cambiando goldens/budgets.
- Un test falla dos veces después de correcciones razonables; reportar el caso y su evidencia.
- El controlador físico manda secuencias incompatibles con el modelo previsto: capturar los bytes y ajustar contrato/tests antes de parchear a ciegas.
- No se puede demostrar build real por falta de SDK/toolchain: continuar gates host independientes, registrar pendiente y detener publicación/instalación/aceptación física.
- La memoria supera el límite acordado, o aparecen pérdidas de nota bajo carga moderada.

## Mantenimiento y ampliaciones posteriores

Agregar parámetros comunes exige direcciones nuevas explícitas en el registro, nunca reindexar las actuales. Los nombres/rangos de E1–E8 deben revisarse al cambiar motores. Los cambios de route o recovery deben invalidar el estado selector. Tests y generador deben usar el mismo registro y mantener anclas independientes contra cambios accidentales de API.

V2 posibles, fuera de este plan: globales con direccionamiento definido para dos unidades; operadores FM6 por NRPN y actualización segura del patch; valores14 bits si existe una necesidad real y soporte de DSP; smoothing por destino; Bank Select de presets propios. No mezclar estas funciones con la primera entrega.

## Fuentes verificadas

- Código local fijado al commit indicado; comandos git/read-only y los extractos de este plan.
- https://midi.org/midi-1-0-control-change-messages : controladores99/98,6/38,101/100 y RPN.
- https://squarp.net/hapax/instr_def/template.txt : sintaxis NRPN MSB:LSB:DEPTH, DEPTH7/14, nombres y secciones.
- https://squarp.net/hapax/manual/modeautomation/ : lanes NRPN, límite64 por pista, tasa ppqn y ausencia de grabación NRPN entrante.

No se auditó de nuevo el resto de motores, seguridad del instalador ni otros forks. No se modificó código, no se corrieron pruebas que escriban archivos, no se compiló paquete y no se conectó/flasheó hardware durante la planificación.
