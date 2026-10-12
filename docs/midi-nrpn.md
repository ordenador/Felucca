# Felucca: NRPN v1 por canal para Hapax

Esta extensión del fork parte de `ef1f561b6b105f20350f6b1eac0dc0789a357f00` (v1.5.1-1). **La release upstream original no implementa estas direcciones.** Las definiciones de este directorio requieren el firmware modificado. Aceptación con Hapax/FM-1 físico pendiente; no se ha flasheado.

## Uso

En Hapax, copiar `docs/hapax/felucca-nrpn-poly.txt` y `felucca-nrpn-drum.txt` al directorio HAPAX de la SD y cargar la definición en la pista. Elegir el puerto de salida y canal; crear manualmente las lanes necesarias en AUTOMATION, seleccionando un destino NRPN con **DEPTH 7**. No se envían valores DEFAULT ni se crean 90 lanes. Hapax admite 64 lanes por pista y no graba NRPN entrante; esta extensión recibe automatización preparada, sin enviar giros del panel como NRPN.

En MENU > MIDI > MIDI IN de Felucca, ROUT CH1-4 resuelve CH1→T1, CH2→T2, CH3→T3, CH4→T4, independientemente de la selección del panel. CH5-8, CH9-12 y CH13-16 resuelven de igual forma sus bloques; descartan todos los bytes de otros canales. En SEL, cada CC6 controla la pista seleccionada **en ese momento**, aunque la selección NRPN se haya enviado antes.

Para dos equipos: A con ROUT CH1-4; B con ROUT CH5-8. En la definición DRUM, el segundo usa **OUTCHAN8 y CH8 en cada una de las ocho DRUMLANES**. Cambiar OUTCHAN no sustituye los canales explícitos de las notas. OUTPORT/INPORT/INCHAN/MAXRATE quedan NULL para configurar el flujo real.

## Mensajes y escala

La dirección es `(MSB << 7) | LSB`. Este banco indica una página de parámetros; **no es MIDI Bank Select**. CC99 selecciona MSB; CC98 selecciona LSB; CC6 envía valor 0…127. Se admiten ambos órdenes de selección y datos repetidos. Cambiar solo un componente reutiliza el otro mientras la selección siga activa. Tras reset, ambos componentes son necesarios. No es preciso enviarlos contiguos.

La escala es la de los CC actuales: `min + floor((value * (max - min) + 63) / 127)`, obtenida del descriptor del parámetro y motor actuales. El valor MIDI tiene siete bits: esto amplía destinos, no la resolución ni el suavizado del DSP. Enums también se cuantizan por esta fórmula; por ejemplo Analog Filter Type 0/64/127 elige LP/BP/HP. PAN 0/64/127 produce −64/0/63. Los índices 0…127 de tiempos, nivel y frecuencias no son necesariamente milisegundos, dB o Hz lineales. Con ENV SYNC, ATK/DEC/REL conservan almacenamiento 0…127 repartido en 25 tiempos musicales; no enviar el índice 0…24 como si fuera directo.

Ejemplo ANALOG CUT de T1, CH1 (bytes hex):

```text
CC99=1   B0 63 01
CC98=4   B0 62 04
CC6=96   B0 06 60
```

Ejemplo FM6 MLVL de T2, CH2, valor neutro:

```text
CC99=1   B1 63 01
CC98=2   B1 62 02
CC6=64   B1 06 40
```

Cerrar mediante RPN Null (CH1):

```text
CC101=127 B0 65 7F
CC100=127 B0 64 7F
```

CC99=127 y CC98=127 es NRPN Null, que invalida la selección solo de esa entrada/canal. Una dirección desconocida sustituye la selección anterior y no escribe ningún parámetro; no recupera el último conocido. CC38 se ignora con NRPN; CC96/97 siguen ignorados. DEPTH14, increment/decrement y operadores FM6 individuales quedan fuera de v1.

## Selección, recuperación y compatibilidad

Hay 32 selectores independientes: USB/TRS × 16 canales. Un MSB USB y un LSB TRS nunca completan una selección. Dos entradas que escriben el mismo parámetro comparten el sonido; gana el último dato válido. RPN0 conserva su estado previo compartido por canal y su prioridad sobre CC6/38. CC99/98 cancelan RPN; CC101/100 cancelan NRPN de ambas entradas de ese canal, incluso RPN desconocido/Null. RPN0 sigue configurando sensibilidad de bend en semitonos (hasta 24) y cents (hasta 99).

CC121 invalida los dos selectores de su canal y conserva parámetros/rango de bend. Cambio de ROUT, power-on y recuperación tras pérdida de datos detectada (overflow de cola MIDI o UART) invalidan todas las selecciones. Un bus reset, suspend o detach USB por sí solo no limpia selectores ni estado de canal; no garantiza recuperar una selección tras desconectar/reconectar. El cliente debe enviar selección completa al comenzar cada sesión y después de reconectar. Después es necesario enviar ambos componentes nuevamente. CC120/123 conservan su comportamiento de silencio/notas, sin redefinir NRPN. Program Change conserva selección; E1–E8 siempre usan el motor actual, y sus etiquetas deben revisarse tras cambiar de motor.

Los CC fijos y los 16 slots MIDI LEARN funcionan igual. Un CC aprendido sigue sustituyendo su función fija; NRPN evita LEARN, no consume slots ni captura `ml_arm`/`ml_heard`. CC y NRPN pueden controlar el mismo destino y gana el último. NRPN usa el setter de CC y las mismas reglas de motion: solo captura valores cambiados de la pista seleccionada, con REC y reproducción activos. No escribe flash ni añade persistencia por mensaje; los valores se guardan por los mecanismos existentes.

POLY conserva CC1/5/6/7/10/11/38/64/71/72/73/74/75/91/93/94/98/99/100/101/120/121/123. DRUM conserva CC1/7/10/11/74/91/93/94/120/121/123. CC1/11 requieren destinos de matriz. CC71/74 siguen dependiendo del motor; el ADSR común no modifica FM6 ni DRUM. Las definiciones no asignan MIDI LEARN implícito ni cambian PC: POLY PC1 es el primer sonido del motor; DRUM PC1…6 corresponde STD/80/10/66/55/77.

## Registro congelado de 90 direcciones

El registro único es `firmware/src/midi_nrpn_map.h`. Los números son API pública y referencian símbolos C, sin depender del orden futuro del enum. Reservados: 0:8, 0:61…80 (también con DIGITAL compilado), 0:103…127, 1:8…127 y MSB2…126. 127:127 es Null. No reutilizar huecos retirados.

| MSB:LSB | Destino | Símbolo C | Valor almacenado |
|---|---|---|---|
| 0:0 | Nivel | `P_LEVEL` | 0…127 |
| 0:1 | ENV Ataque | `P_ATK` | 0…127 |
| 0:2 | ENV Decaimiento | `P_DEC` | 0…127 |
| 0:3 | ENV Sostenido | `P_SUS` | 0…127 |
| 0:4 | ENV Liberacion | `P_REL` | 0…127 |
| 0:5 | ENV Filtro | `P_ED_FLT` | -64…63 |
| 0:6 | ENV Tono | `P_ED_PIT` | -64…63 |
| 0:7 | ENV Forma | `P_ED_SHP` | -64…63 |
| 0:9 | LFO Frecuencia | `P_LRATE` | 0…127 |
| 0:10 | LFO Onda | `P_LWAVE` | 0…4 (enum) |
| 0:11 | LFO Fase | `P_LPHASE` | 0…127 |
| 0:12 | LFO Entrada | `P_LFADE` | 0…127 |
| 0:13 | LFO Tono | `P_LD_PIT` | -64…63 |
| 0:14 | LFO Filtro | `P_LD_FLT` | -64…63 |
| 0:15 | LFO Forma | `P_LD_SHP` | -64…63 |
| 0:16 | LFO Amplitud | `P_LD_AMP` | 0…127 |
| 0:17 | Arp Modo | `P_AMODE` | 0…14 (enum) |
| 0:18 | Arp Frecuencia | `P_ARATE` | 0…9 (enum) |
| 0:19 | Arp Octavas | `P_AOCT` | 1…4 |
| 0:20 | Arp Duracion | `P_AGATE` | 1…127 |
| 0:21 | Arp Swing | `P_ASWING` | 0…100 |
| 0:22 | Arp Probabilidad | `P_APROB` | 0…127 |
| 0:23 | Arp Retener | `P_AHOLD` | 0…1 (enum) |
| 0:24 | Arp Orden | `P_AORDER` | 0…1 (enum) |
| 0:25 | Escala Raiz | `P_ROOT` | 0…11 |
| 0:26 | Escala | `P_SCALE` | 0…15 (enum) |
| 0:27 | Cuantizar | `P_QUANT` | 0…3 (enum) |
| 0:28 | Transposicion | `P_TRANS` | -24…24 |
| 0:29 | Secuencia Longitud | `P_SLEN` | 1…64 |
| 0:30 | Secuencia Division | `P_SDIV` | 0…9 (enum) |
| 0:31 | Secuencia Swing | `P_SSWING` | 0…100 |
| 0:32 | Secuencia Duracion | `P_SGATE` | 1…127 |
| 0:33 | Distorsion | `P_DIST` | 0…127 |
| 0:34 | Envio Chorus | `P_CHOR` | 0…127 |
| 0:35 | Envio Delay | `P_DLY` | 0…127 |
| 0:36 | Envio Reverb | `P_REV` | 0…127 |
| 0:37 | Voz Modo | `P_VOICE` | 0…3 (enum) |
| 0:38 | Portamento | `P_GLIDE` | 0…127 |
| 0:39 | Panorama | `P_PAN` | -64…63 |
| 0:40 | Silencio | `P_MUTE` | 0…1 (enum) |
| 0:41 | Portamento Modo | `P_GLMODE` | 0…1 (enum) |
| 0:42 | Voz Prioridad | `P_PRIO` | 0…2 (enum) |
| 0:43 | Voz Asignacion | `P_ALLOC` | 0…1 (enum) |
| 0:44 | Desafinacion | `P_DETUNE` | 0…127 |
| 0:45 | Slicer Modo | `P_SLCR` | 0…2 (enum) |
| 0:46 | Slicer Patron | `P_SLPAT` | 1…16 |
| 0:47 | Slicer Frecuencia | `P_SLRATE` | 0…5 (enum) |
| 0:48 | Slicer Profundidad | `P_SLDEPTH` | 0…127 |
| 0:49 | Matriz1 Fuente | `P_M1SRC` | 0…10 (enum) |
| 0:50 | Matriz1 Destino | `P_M1DST` | 0…20 (enum) |
| 0:51 | Matriz1 Cantidad | `P_M1AMT` | −64…63 |
| 0:52 | Matriz2 Fuente | `P_M2SRC` | 0…10 (enum) |
| 0:53 | Matriz2 Destino | `P_M2DST` | 0…20 (enum) |
| 0:54 | Matriz2 Cantidad | `P_M2AMT` | −64…63 |
| 0:55 | Matriz3 Fuente | `P_M3SRC` | 0…10 (enum) |
| 0:56 | Matriz3 Destino | `P_M3DST` | 0…20 (enum) |
| 0:57 | Matriz3 Cantidad | `P_M3AMT` | −64…63 |
| 0:58 | Matriz4 Fuente | `P_M4SRC` | 0…10 (enum) |
| 0:59 | Matriz4 Destino | `P_M4DST` | 0…20 (enum) |
| 0:60 | Matriz4 Cantidad | `P_M4AMT` | −64…63 |
| 0:81 | Acorde | `P_CHRD` | 0…9 (enum) |
| 0:82 | Voces Acorde | `P_VOIC` | 0…4 (enum) |
| 0:83 | Bateria Bombo | `P_LN0` | 0…127 |
| 0:84 | Bateria Caja | `P_LN1` | 0…127 |
| 0:85 | Bateria Palmas | `P_LN2` | 0…127 |
| 0:86 | Bateria Hat Cerrado | `P_LN3` | 0…127 |
| 0:87 | Bateria Hat Abierto | `P_LN4` | 0…127 |
| 0:88 | Bateria Tom | `P_LN5` | 0…127 |
| 0:89 | Bateria Aro | `P_LN6` | 0…127 |
| 0:90 | Bateria Campana | `P_LN7` | 0…127 |
| 0:91 | LFO Sync | `P_LSYNC` | 0…10 (enum) |
| 0:92 | LFO Disparo | `P_LTRIG` | 0…1 (enum) |
| 0:93 | LFO Polaridad | `P_LPOL` | 0…1 (enum) |
| 0:94 | Secuencia Cuantizar | `P_SQNT` | 0…1 (enum) |
| 0:95 | Apertura | `P_SPRD` | 0…127 |
| 0:96 | Insert Tipo | `P_ITYPE` | 0…8 (enum) |
| 0:97 | Insert A | `P_IA` | 0…127 |
| 0:98 | Insert B | `P_IB` | 0…127 |
| 0:99 | Insert C | `P_IC` | 0…127 |
| 0:100 | Insert Mezcla | `P_IMIX` | 0…127 |
| 0:101 | Analog Filtro Tipo | `P_FTYPE` | 0…2 (enum) |
| 0:102 | ENV Sync | `P_ESYNC` | 0…1 (enum) |
| 1:0 | Motor E1 | `P_E0` | Según motor; ver ejemplos abajo |
| 1:1 | Motor E2 | `P_E1` | Según motor; ver ejemplos abajo |
| 1:2 | Motor E3 | `P_E2` | Según motor; ver ejemplos abajo |
| 1:3 | Motor E4 | `P_E3` | Según motor; ver ejemplos abajo |
| 1:4 | Motor E5 | `P_E4` | Según motor; ver ejemplos abajo |
| 1:5 | Motor E6 | `P_E5` | Según motor; ver ejemplos abajo |
| 1:6 | Motor E7 | `P_E6` | Según motor; ver ejemplos abajo |
| 1:7 | Motor E8 | `P_E7` | Según motor; ver ejemplos abajo |

### Ejemplos E1–E8

Las etiquetas genéricas Motor E1…Motor E8 permiten reutilizar las definiciones. Renombrarlas en Hapax según el motor de esa pista:

| Dirección | ANALOG | Rango almacenado | FM6 | Rango almacenado |
|---|---|---|---|---|
| 1:0 | WAVE | 0…6 | ALG | 0…32 |
| 1:1 | DTN | 0…127 | FB | −7…7 |
| 1:2 | MIX | 0…127 | MLVL | −64…63 |
| 1:3 | NOIS | 0…127 | MRAT | −16…16 |
| 1:4 | CUT | 0…127 | MEG | −64…63 |
| 1:5 | RES | 0…127 | VMOD | −7…7 |
| 1:6 | DRV | 0…127 | DTUN | 0…127 |
| 1:7 | KTR | 0…127 | SLOT | 0…40 |

FM6 ALG0 usa el algoritmo del patch; SLOT0…7=F1…F8, SLOT8=OWN, SLOT9…40=B1…B32. NRPN escala 0…127 al rango; no modifica la semántica de slots/banco. MLVL/MRAT/MEG son macros de patch; no bytes individuales de los operadores. Los niveles Bateria son exclusivos de DRUM; Analog Filter Type es exclusivo de ANALOG. Exponer un parámetro no activa funciones que un motor ignore.

## Tasas y pruebas pendientes

Comenzar la prueba física con cuatro lanes a 8 ppqn y 120 BPM (hasta 16 actualizaciones/s por lane), después ocho lanes, notas y clock. Capturar los mensajes reales y medir pérdidas/latencia/ruido. Una selección completa más dato son tres CC: nueve bytes, unos 2,88 ms en DIN 31.250 bps sin running status; ocho lanes a 16 cambios/s llegan a 1.152 bytes/s antes de notas/clock si todas reenvían selección. No asumir si Hapax reenvía/omite selectores. La memoria adicional de selección es 96 B; el registro común ocupa 256 B constantes. No se promete automatización ilimitada.

Reproducir generación: `python3 tools/gen_hapax_nrpn.py`; validar sin escritura: `python3 tools/gen_hapax_nrpn.py --check` y `python3 tests/hapax_nrpn_test.py`. Resultados y limitaciones: `plans/evidence/001-nrpn-hapax.md`. No flashear automáticamente por haber pasado pruebas host.

Fuentes de sintaxis y comportamiento Hapax: [plantilla oficial](https://squarp.net/hapax/instr_def/template.txt), [automatización](https://squarp.net/hapax/manual/modeautomation/). Protocolo MIDI: [Control Change](https://midi.org/midi-1-0-control-change-messages).
