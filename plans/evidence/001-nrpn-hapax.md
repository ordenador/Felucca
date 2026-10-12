# Evidencia Plan 001 — NRPN por canal / Hapax

Resultado final: implementación revisada, build real y suite final PASS, sin flasheo. Véase el cierre al final y el registro reproducible [001-qa-status.json](001-qa-status.json).

Fecha: 11 de octubre de 2026, America/Santiago.
Estado: **IN PROGRESS** para aceptación física; implementación, build real y revisión de software terminados. Suite final exit 0; dos UB preexistentes documentados abajo. Autorización de Mario: implementar y probar, **sin flashear**. No hubo commits, push ni PR.

## Identidad y alcance

- Worktree aislado: `/Users/mfaundez/git/github/Felucca-worktrees/midi-nrpn-per-channel`.
- Rama: `feat/midi-nrpn-per-channel`; HEAD base `ef1f561b6b105f20350f6b1eac0dc0789a357f00`.
- El checkout principal y los cambios locales de Mario quedaron fuera del trabajo.
- Código modificado únicamente en `midi_control.c` y `seq.c`; registro nuevo `midi_nrpn_map.h`. `core.h`, parámetros, motores, DSP, persistencia, HAL, UART/USB, editor y goldens/budgets intactos.
- 82 direcciones comunes explícitas y ocho de motor; símbolos C estables, 90 nombres únicos. Map común uint16[128] usa id+1 para permitir P_LEVEL=0 y reserva huecos. Ocho parámetros de motor se resuelven desde P_E0, con validación id<P_COUNT.

## Baseline y pruebas host

Desde la raíz del worktree:

```sh
mkdir -p build/host
cc -O1 -Wall -Wno-unused-function -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test tests/midi_control_test.c -lm
build/host/midi_control_test
```

Antes de editar: compilación y ejecución exit 0, `MIDI control/clock integration tests passed`. Warnings existentes de stubs/headers host (memset/memcpy, punteros de hardware, variables, expresión y seed), sin modificar esos archivos. Después de integrar NRPN, todas las pruebas existentes CC/LEARN/RPN/PC/expresión/sustain/transporte siguen pasando sin eliminar verificaciones. Resultado actualizado en `build/host/midi-nrpn.log`.

Cobertura añadida mediante la cola y UART reales:

- Selección parcial, ambos órdenes, address/value cero, datos repetidos, reutilización de componente, USB/TRS independientes y source desconocido.
- 90 destinos 0/64/127, todas las 16.384 direcciones (16.294 desconocidas sin escritura), anclas numéricas congeladas y parámetros E1–E8 ANALOG/FM6.
- Cuatro pistas y todos los bloques CH1-4/5-8/9-12/13-16, canales externos descartados y resolución SEL al recibir CC6.
- CC121 por canal, ruta en ambos sentidos, power-on, overflow, RPN0/clamping/cents, RPN desconocido/Null y NRPN Null.
- CC/NRPN al mismo destino, CC aprendido con prioridad, LEARN lleno/armado sin capturar NRPN, PC y motion sin cambios de reglas.
- Running status TRS con realtime intercalado; estrés de 10.000 cambios válidos con notas, bend, sustain, CC y clock, sin owners retenidos y valores finales exactos; recuperación por overflow en prueba separada.

Comandos de variantes:

```sh
cc -O1 -w -DFELUCCA_SLICE=0 -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test_slice0 tests/midi_control_test.c -lm
build/host/midi_control_test_slice0
cc -O1 -w -DFELUCCA_FM4=1 -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test_fm4 tests/midi_control_test.c -lm
build/host/midi_control_test_fm4
```

Ambas variantes compilaron y ejecutaron con exit 0. Logs `build/host/midi-nrpn-slice0.log` y `midi-nrpn-fm4.log`. DIGITAL legacy conserva todos sus huecos NRPN excluidos.

## Sanitizers: limitación preexistente reproducida

```sh
cc -O1 -w -g -fsanitize=address,undefined -fno-omit-frame-pointer -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test_asan tests/midi_control_test.c -lm
ASAN_OPTIONS=detect_leaks=0 build/host/midi_control_test_asan
```

Compilación/ejecución exit 0 y tests pasan, sin diagnósticos AddressSanitizer. **No es una ejecución UBSan limpia**: dos left-shifts de negativos en `eng_analog.c:177` y `:179` (−266 y −8). Se repitió la misma compilación/ejecución en el baseline original creado con `git archive HEAD`, y se reprodujeron exactamente los mismos diagnósticos/valores. Logs `build/host/midi-baseline-asan.log` y `midi-nrpn-asan.log`. No se suprimieron checks ni se modificó DSP fuera de alcance. Este hallazgo queda pendiente preexistente y es la desviación del gate ideal “sanitizers sin diagnósticos”.

## Definiciones y generación

```sh
python3 tools/gen_hapax_nrpn.py
python3 tools/gen_hapax_nrpn.py --check
python3 tests/hapax_nrpn_test.py
```

Exit 0; unittest 4/4 OK. Generador stdlib y determinista; --check no escribe. Tests validan las 90 direcciones, hash congelado de direcciones/símbolos, nombres únicos ASCII, DEPTH7, CC intactos, lanes canónicas/CH4, PC, encabezados, COMMENT/TRACKNAME y ausencia de DEFAULT/ASSIGN/AUTOMATION. Corrupciones intencionadas de duplicación/dirección/DEPTH/default/nombre/comentario se rechazan; en copias temporales con drift, --check devuelve 1 sin alterar bytes. Un fallo inicial del test nuevo para sección DRUMLANES vacía se corrigió en el parser del test; las pruebas originales no se modificaron para hacerlas pasar.

Artefactos: `docs/hapax/felucca-nrpn-poly.txt`, `felucca-nrpn-drum.txt`; protocolo y tabla completa en `docs/midi-nrpn.md`. Son exclusivos del fork NRPN, sin sobrescribir las definiciones de revisión anteriores de Mario.

## Toolchain y build real

No se encontró instalación existente de toolchain JieLi/SDK AC79 en las rutas buscadas. Docker, Pillow y Emscripten `/opt/homebrew/bin/emcc` (6.0.12) ya estaban disponibles. Se prepararon dependencias aisladas en `build/deps/` (ignoradas), sin cambiar HOME/CODEX_HOME ni instalar en el sistema:

- JieLi `jieli-linux-toolchains-20260730.1`, ruta `build/deps/jieli/toolchain`.
- SDK AC79: únicamente los tres archivos requeridos por `tools/build.py`, todos SHA256 comprobados contra sus pins.
- Python venv `build/deps/python/bin/python`, Pillow existente y fontTools instalado aislado.
- Docker amd64 disponible para compilar pi32v2 desde macOS.

El revisor ejecutó baseline con código HEAD en `build/baseline`, luego build del cambio:

```sh
JIELI_TOOLCHAIN="$PWD/build/deps/jieli/toolchain" AC79_SDK="$PWD/build/deps/ac79" PYTHON="$PWD/build/deps/python/bin/python" ./build.sh
```

Ambos exit 0; logs `build/baseline-build.log` y `build/nrpn-build.log`.

| Métrica real | Baseline | NRPN | Diferencia |
|---|---:|---:|---:|
| Imagen app | 495580 B | 496108 B | +528 B |
| RAM .data+.bss | 54964 B | 55060 B | +96 B |
| Pool DSP | 327800 B | 327800 B | 0 B |
| Loader ota.bin | 6930 B | 6930 B | 0 B |
| Paquete fwsc | 610086 B | 610086 B | 0 B |

RAM libre respecto al límite: 18668 B. El test de sizeof confirma selector 96 B y mapa común 256 B constantes. Aumento de estado estático 96 B, bajo límite 256 B; no nuevas strings en imagen por los nombres del registro. Paquete con tamaño fijo no implica app idéntica.

SHA256 del paquete NRPN `build/felucca.fwsc`: `cbf860b88066f03ab68165aa8a0658eb1465f5cbae75b5d52372899794c50087`.
SHA256 app `build/felucca.bin`: `7498bda361bc0ecca979fd867aee52db50fbf22aa5f01e8753f88358654e86d0`.

Regresión completa: primera ejecución exit 0 en `build/nrpn-suite.log`. Después de añadir ráfagas reales y MIDI al gate SAN, el revisor repitió la suite completa: exit 0, `ALL HOST TESTS PASSED`, log `build/nrpn-suite-final.log`. No se editaron goldens ni budgets por fallos. Omisiones y límites detallados en el cierre de revisión.

## Hardware y finalización

**No se flasheó ni se conectó hardware para probar el cambio.** Pendiente etapa 6 del plan: versiones/unidades/backup, importación Hapax, dos equipos CH1-4 y CH5-8, USB y DIN/TRS, carga MIDI medida, diez minutos sin notas colgadas y restauración. Sin esa evidencia no declarar aceptación física.

`git diff --check`: exit 0 tras documentación/generador. No commits, push, PR ni ramas codex/. El revisor actualiza índice/estado y verifica alcance al terminar suite/revisión.


## QA adicional — ráfagas reales y gate SAN de MIDI

Revisión adicional autorizada por Mario: cerrar cobertura de ingreso real y agregar MIDI al perfil sanitizer existente, sin modificar núcleo, DSP, USB/UART, web/emu, goldens ni budgets.

- `tests/run_tests.sh`: el bucle SAN ahora incluye `midi_control_test`. **Perfil y exclusiones originales intactos**: `-fsanitize=address,undefined -fno-sanitize=signed-integer-overflow,shift,bounds,object-size,pointer-overflow -fno-sanitize-recover=undefined`.
- Nuevo `nrpn_burst_test`: USB entra por `ep1_take`; TRS por `um_byte` con running status y realtime intercalado. Se encolan selectores/datos de ambas fuentes antes de una sola llamada `events_block`, sin helpers que drenen cada mensaje. Un MSB USB y un LSB TRS del mismo canal no se combinan; selecciones completas coexistentes escriben destinos distintos del mismo canal.
- Verificados Data Entry repetidos, último writer CC/NRPN, bend, note-on USB/note-off TRS y ownership; 16 batches de 24 eventos cada uno, ambas fuentes en **cada uno de los cuatro canales**, alternando el orden de fuentes. Esta prueba no correlaciona fuente con canal como el estrés original.
- Overflow real mediante `um_byte` en una cola llena entre selección y Data Entry; datos posteriores y selección de un solo componente no escriben. Reselección completa restaura escritura en ambas fuentes. También pérdida detectada del DMA UART mediante `uart_midi_take(UM_RING+1)` invalida selectores.

Comandos exactos (desde la raíz del worktree):

```sh
cc -O1 -w -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test tests/midi_control_test.c -lm
build/host/midi_control_test > build/host/midi-nrpn-extraqa.log 2>&1
cc -O1 -w -DFELUCCA_SLICE=0 -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test_slice0 tests/midi_control_test.c -lm
build/host/midi_control_test_slice0 > build/host/midi-nrpn-extraqa-slice0.log 2>&1
cc -O1 -w -DFELUCCA_FM4=1 -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test_fm4 tests/midi_control_test.c -lm
build/host/midi_control_test_fm4 > build/host/midi-nrpn-extraqa-fm4.log 2>&1
cc -O1 -g -fsanitize=address,undefined -fno-sanitize=signed-integer-overflow,shift,bounds,object-size,pointer-overflow -fno-sanitize-recover=undefined -w -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test_san tests/midi_control_test.c -lm
ASAN_OPTIONS=detect_leaks=0 build/host/midi_control_test_san > build/host/midi-nrpn-extraqa-san.log 2>&1
python3 tools/gen_hapax_nrpn.py --check
python3 tests/hapax_nrpn_test.py
git diff --check
```

Todos estos comandos terminaron con exit 0. Los cuatro logs MIDI terminan en `MIDI control/clock integration tests passed`; el perfil SAN existente no reportó diagnósticos. Definiciones 4/4 OK y diff sin errores. El run estricto anterior y sus dos UB baseline siguen documentados arriba; el perfil existente excluye shifts y por ello **no equivale a UBSan estricto limpio**. El run estricto final también terminó con exit 0 y todos los tests OK, pero mantiene exactamente los dos diagnósticos baseline de shifts negativos (−266 y −8), sin diagnósticos ASan ni UB adicionales. Log `build/host/midi-nrpn-extraqa-strict.log`.

```sh
cc -O1 -w -g -fsanitize=address,undefined -fno-omit-frame-pointer -Ibuild/gen -Ifirmware/src -o build/host/midi_control_test_asan tests/midi_control_test.c -lm
ASAN_OPTIONS=detect_leaks=0 build/host/midi_control_test_asan > build/host/midi-nrpn-extraqa-strict.log 2>&1
```

No se deshabilitó ningún check para este run estricto. El éxito del proceso no elimina esos diagnósticos preexistentes.

### Desconexión/reconexión USB: límite por inspección

Se precisó `docs/midi-nrpn.md`: invalidación por power-on, CC121/RPN, cambio ROUT y **pérdida de datos detectada** (overflow de cola MIDI o UART). No hay garantía de invalidación por desconectar/reconectar USB. Inspección de `usb_poll` (`firmware/src/usb.c`, ramas suspend/reset) y `usb_detach` confirma que no llaman `midi_nrpn_reset` ni limpian `midi_ch`; `rg -n midi_nrpn_reset firmware/src/usb.c firmware/src/seq.c firmware/src/midi_control.c` confirma resets en control/seq, ninguno en USB. El cliente debe enviar selección completa al empezar una sesión o reconectar.

No se ejecutó `usb_poll`/bus reset en host: el harness actual incluye HAL real y acceso SIE/registers memory-mapped (`fm1_usb.h`), y `tests/uac_test.c` explícitamente evita `usb_poll`. Simularlo exigiría nuevos stubs/driver fuera del alcance aprobado. Este punto es evidencia por inspección, no una aceptación dinámica del bus. **Sin hardware ni flasheo**; continúa pendiente la aceptación física completa.


## QA adicional — persistencia NRPN con NOR habilitada

Se creó una prueba aislada ignorada en `build/host/nrpn_persistence_test.c`, sin modificar firmware, tests tracked ni `run_tests.sh` mientras la suite final se ejecuta. Aprovecha el prefijo de `tests/backup_test.c` anterior a su `main` (incluye hostsim, UI y `storage.c`/`upreset.c`/`project.c` reales con **FELUCCA_FLASH=1**). El backend es NOR de 1 MiB **en RAM del host**, con erase a 0xFF y programación únicamente 1→0; cuenta operaciones erase/program. No usa el driver flash físico.

Ingreso de once destinos representativos mediante `ep1_take` USB y `um_byte` TRS, seguido de `events_block`: nivel/pan/ADSR, bipolar de matriz, enums INSERT/filter/ENV SYNC, ANALOG CUT, FM6 MLVL/feedback y nivel de lane DRUM. Anclas numéricas independientes incluyen pan −45, matriz −47, FM6 MLVL −32 y enums concretos. Las pruebas no dependen únicamente de RAM retenida:

1. Selecciones y Data Entry NRPN no cambian ni un byte de la NOR simulada ni sus contadores erase/program.
2. `project_save_as` escribe NOR; `st_load`/`proj_import` confirman formato **FUNA, 3840 B**, magic `0x46554E41`, size y valores exactos.
3. Se destruyen `proj_slot`, tracks y motion de RAM; `project_load` debe obtener de NOR y restaurar los once valores NRPN.
4. `up_store` escribe banco NOR y mantiene **UPB1, versión4, record192 B, P_COUNT111**. Payload conserva todos los valores T1, incluidos nivel y pan bipolar; se borra el banco RAM y `up_boot`/`up_load` restauran valores de sonido. Los controles del mixer se conservan según la semántica preexistente del preset, y se verifica esa excepción explícitamente.
5. NRPN graba una automation de CUT mientras REC/PLAY activos sin escribir NOR. STOP restaura la base. Se guarda el proyecto, destruyen copias RAM y carga de NOR: motion vuelve byte-for-byte. Al iniciar la secuencia real, CUT toma el valor grabado27; STOP restaura la base original.

Quince checks pasan. Comandos (raíz del worktree):

```sh
cc -O1 -w -Itests -Ibuild/gen -Ifirmware/src -o build/host/nrpn_persistence_test build/host/nrpn_persistence_test.c -lm
build/host/nrpn_persistence_test > build/host/nrpn-persistence.log 2>&1
```

Compilación/ejecución exit 0; log termina `NRPN NOR persistence test passed`. El `.c` completo queda disponible en build/host para revisión/reproducción con la misma base. Es QA aislada, todavía no incorporada al runner; la suite final continúa a cargo del revisor. No se tocaron exclusiones SAN, goldens/budgets, build/gen ni web/emu. También se compiló/ejecutó el perfil SAN existente sobre este harness: exit 0, quince checks PASS y sin diagnósticos. Log `build/host/nrpn-persistence-san.log`.

```sh
cc -O1 -g -fsanitize=address,undefined -fno-sanitize=signed-integer-overflow,shift,bounds,object-size,pointer-overflow -fno-sanitize-recover=undefined -w -Itests -Ibuild/gen -Ifirmware/src -o build/host/nrpn_persistence_test_san build/host/nrpn_persistence_test.c -lm
ASAN_OPTIONS=detect_leaks=0 build/host/nrpn_persistence_test_san > build/host/nrpn-persistence-san.log 2>&1
```

SHA256 fuente aislada: `a4f510230b4b12b8b222034eb1d4fef3f638c3d62a4a12bef8da3c16a779c11d`. El perfil SAN y sus exclusiones son las del repositorio; esto no cambia los diagnósticos del run estricto de MIDI documentados anteriormente.

Limitaciones: once destinos representativos, no cada posible patch ni escenario de power-cut. Persistencia/formatos antiguos y cortes se cubren separadamente por la suite existente. La prueba host **no escribe flash real y no flashea hardware**; aceptación Hapax/FM-1 sigue pendiente.


## Cierre de revisión — versión final

Revisor: software **APPROVE con desviación UBSan baseline documentada**. El alcance solicitado de implementar, compilar y probar sin flashear está terminado. El plan conserva IN PROGRESS exclusivamente porque su aceptación física exige Hapax/FM-1; no se ha ejecutado esa etapa.

La suite final se ejecutó después de cerrar las modificaciones del runner y de las pruebas de ráfagas:

```sh
env PATH="$PWD/build/deps/python/bin:$PATH" AC79_SDK="$PWD/build/deps/ac79" sh tests/run_tests.sh > build/nrpn-suite-final.log 2>&1
node build/qa-nrpn-wasm.mjs > build/qa-nrpn-wasm-final.log 2>&1
```

Ambos exit 0. Suite: `ALL HOST TESTS PASSED`, 96 gates ejecutados. Incluye regresión/goldens, coste pi32v2, UI, persistencia, protocolos de loader/OTA simulados, MIDI/NRPN dentro del perfil SAN existente, fuzz SysEx/USB de 20000 iteraciones (seed7), proyectos5000 (seed13), muestras1000 (seed17), tests web y build/tests WASM. No se renovaron goldens ni budgets. WASM y nativo producen 88200 frames idénticos; el escenario pesado midió 12.2 ms por segundo de audio en este host (no rendimiento del chip).

QA NRPN WASM adicional: once checks por exports públicos, audio NRPN/CC idéntico para ANALOG CUT/PAN y FM6 MLVL; selección incompleta/desconocida, RPN Null, routing, ráfagas y overflow; 10000 actualizaciones con salida finita. Solo entrada USB lógica, sin periféricos emulados. Se repitió sobre el WASM de la suite final.

El revisor recompiló y ejecutó también el harness NOR de quince checks, normal y con el perfil SAN existente, ambos exit0 (`build/host/review-nrpn-persistence{,-san}.log`). Fuente aislada y comandos indicados arriba. Comprueba once destinos representativos, no los90 individualmente. Sin hardware.

### PASS / desviaciones / SKIP

- **PASS:** build firmware; todos los gates ejecutados por la suite final; variantes MIDI SLICE0/FM4; registro y definiciones Hapax4/4; QA WASM/NOR adicional; `git diff --check`; fuente congelada sin drift; protección de loader/boot head y demás firmware.
- **Desviación conocida:** UBSan estricto detecta dos shifts negativos ANALOG idénticos al baseline; cero diagnósticos nuevos/ASan. El perfil SAN del repositorio conserva exclusiones `signed-integer-overflow,shift,bounds,object-size,pointer-overflow`. Su PASS no significa UBSan estricto limpio.
- **SKIP:** comparación PHYS contra DaisySP (checkout ausente); restore de paquete oficial V15 (FM-1_v15.fwsc ausente); MENU settings, sender de banco FM6 y mapa MIDI LEARN del editor legacy (funciones ausentes de ese editor). Los tests firmware de esas capacidades sí se ejecutan donde existen.
- **SKIP físico:** importación Hapax, USB/TRS reales, carga/jitter del chip y reproducción prolongada. Prohibición expresa de flasheo en esta entrega. Bus reset USB solo inspeccionado, como se explicó arriba.

### Asociación de fuente y artefactos

Registro completo: `plans/evidence/001-qa-status.json`, con hashes de255 archivos, diff tracked, artefactos, gates y omisiones. Base `ef1f561b6b105f20350f6b1eac0dc0789a357f00`, rama `feat/midi-nrpn-per-channel`, cambios locales sin commit.

Fingerprint de fuente/tests/docs excluyendo build/planes: `37703bc331f2ef8f896e94039d0d9d2286262eb19e029112de06d598e13798a5`. Diff tracked SHA256: `516d503b1e1e81c446a3b64dcef55a22ea072c9b32d9b5ddac4f87d220d0cbb6`. Se verificó sin drift después de todas las pruebas.

Paquete de desarrollo: `build/felucca-nrpn-v1-dev.fwsc` (610086B), SHA256 `cbf860b88066f03ab68165aa8a0658eb1465f5cbae75b5d52372899794c50087`; archivo compañero `.SHA256SUMS`. Es el paquete compilado, sin instalar. Identidad de empaquetado de desarrollo FM-1_900; la pantalla conserva versión base v1.5.1, por lo que el nombre y hash identifican esta variante.

`ota.bin` es idéntico al baseline (6930B, SHA256 `a48ee499520cb16750e2504264bd8a8cd3e13ea953bbf319537cb840eb0d2115`). Primeros16KiB de **flash.bin extraído y CRC validado del UFW**, idénticos: `53144a0a192b505e30cbdba2477c9771a05564cd7b6441ca12e85f16ca88b077`. No se comparó un offset arbitrario del contenedor. Resto de firmware tracked coincide con base, excepto `midi_control.c` y `seq.c`; único header nuevo `midi_nrpn_map.h`.

La QA de otra sesión sobre el snapshot anterior está en `/Users/mfaundez/git/github/Felucca-worktrees/firmware-safety-audit/plans/nrpn-independent-qa.md`: reconstruyó un binario idéntico y ejecutó probes adversos adicionales. Sus hashes de snapshot son propios y no sustituyen este registro final.

Checkout principal permanece en main con código sin modificar y conserva `LOCAL-RUN.md` y `start-felucca.command`. No commits, push, PR, cambios de ramas del checkout principal ni accesos a dispositivos.


## Publicación autorizada después de QA

Mario autorizó hacer commit y push a `origin` (`ordenador/Felucca`) en `feat/midi-nrpn-per-channel`, sin flashear. Las afirmaciones anteriores sobre ausencia de commits/push describen la fase de implementación y verificación previa a esta autorización. Antes de publicar se volvió a comprobar que los 255 archivos y los artefactos coinciden con los hashes probados, además de `git diff --check`. No se incluye `build/`, dependencias ni paquetes binarios en Git. La aceptación física sigue pendiente.
