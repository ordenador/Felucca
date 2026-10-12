> Registro de QA realizado antes del commit. Las menciones a cambios sin commit/push describen esa fase histórica. Mario autorizó posteriormente publicar el fix en `ordenador/Felucca:fix/analog-ubsan-signed-shifts`, manteniendo la prohibición de flasheo.

# ANALOG: shifts negativos corregidos y QA final

Fecha: 12 de octubre de 2026, America/Santiago.
Resultado: **PASS del alcance software**, sin flasheo ni acceso a dispositivos.
Cambio local sin commit/push en `fix/analog-ubsan-signed-shifts`, worktree
`/Users/mfaundez/git/github/Felucca-worktrees/analog-ubsan-signed-shifts`.
Base NRPN: `b3fdf11d92659f6aa7f1b8965f8669f77b78edfd`.

## Problema y corrección

El MIDI estricto del baseline reproduce los dos shifts de muestras negativas
ANALOG registrados ayer. El barrido ampliado del motor detecta cinco expresiones
con el mismo defecto, en las líneas originales 107/108, 131, 177/179: las rutas
normales y SYNC/SUB duplicaban muestras signed con `<<1`; PWM convertía a unsigned
solo después de desplazar un offset que puede ser negativo.

Se sustituyeron los cuatro escalados por `*2` y se movió la conversión unsigned
antes del shift PWM. La soft knee acota la muestra y el contrato Q15 de amplitud
mantiene los productos en int32; el cálculo de fase ahora utiliza wrap unsigned
definido. No cambia el orden de operaciones, la cuantización, los filtros ni las
reglas MIDI/persistencia.

Único archivo de firmware cambiado: `firmware/src/eng_analog.c` (cinco líneas).
Prueba nueva `tests/analog_ubsan_test.c`; runner ampliado con un gate de audio y
con ASan+UBSan estrictos para ANALOG y MIDI/NRPN, sin exclusiones y con
`-fno-sanitize-recover=all`. El perfil amplio heredado conserva sus exclusiones
para otros caminos; no se declara ausencia global de UB de todo el firmware.

## Reproducción y audio

Baseline MIDI: proceso exit0 con dos diagnósticos UB (el modo recuperable no
certifica limpieza). Baseline motor ampliado: exit0 con cinco diagnósticos UB.
Con `UBSAN_OPTIONS=halt_on_error=1`, el baseline se detiene con exit134/SIGABRT,
como reproducción negativa esperada. Logs archivados `baseline-*.log`.

El sweep de 1890 casos ejercita siete waves, tres taps de filtro, cinco shapes
PWM a ambos lados del centro, tres notas, tres configuraciones de
cutoff/resonancia/noise/drive y amplitud constante/rampa. No es un barrido de
cada combinación posible. Renderiza 725760 muestras, con 410352 negativas y
313949 positivas. Hash pre-fix y fix: `aea76a7387be2d18`.
El modo normal exige ese hash; `--dump` se usó explícitamente para capturar el
baseline y no se utiliza en los gates de aceptación.

Durante el diseño del test, un límite inicial 65536 resultó incorrecto para la
convención `VOICE_FS=24000` y los dos escalados del motor. Se corrigió a
`4*VOICE_FS` antes de congelar el baseline y antes de modificar el firmware.
No fue una regresión de Felucca ni se relajaron goldens/budgets existentes.

## Comandos y resultados

Desde la raíz del worktree nuevo, con dependencias existentes comprobadas:

```sh
JIELI_TOOLCHAIN=/Users/mfaundez/git/github/Felucca-worktrees/midi-nrpn-per-channel/build/deps/jieli/toolchain AC79_SDK=/Users/mfaundez/git/github/Felucca-worktrees/midi-nrpn-per-channel/build/deps/ac79 PYTHON=/Users/mfaundez/git/github/Felucca-worktrees/midi-nrpn-per-channel/build/deps/python/bin/python ./build.sh > build/analog-fixed-build.log 2>&1
env PATH="/Users/mfaundez/git/github/Felucca-worktrees/midi-nrpn-per-channel/build/deps/python/bin:$PATH" AC79_SDK=/Users/mfaundez/git/github/Felucca-worktrees/midi-nrpn-per-channel/build/deps/ac79 sh tests/run_tests.sh > build/analog-fixed-suite.log 2>&1
```

Ambos exit0. Suite final: **99 gates**, `ALL HOST TESTS PASSED`.
92 renders golden: 0 cambios, 0 errores health/voces/routing/CPU y 0 crashes.
Incluye UI y renders, persistencia/formatos/backup, loader/OTA simulados, MIDI,
strict ANALOG/MIDI, SAN heredado, fuzz SysEx/USB 20000 seed7, proyectos 5000 seed13,
muestras 1000 seed17, budgets pi32v2, CLI simulado, web y WASM.
WASM/nativo: 88200 frames idénticos. El tiempo observado de 16.5 ms por segundo de
canción pesada pertenece a este host, no al chip.

Comandos manuales de contraste estricto (sin `-fno-sanitize`):

```sh
cc -O1 -w -g -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -Ibuild/gen -Ifirmware/src -o build/host/analog-fixed-sweep-strict tests/analog_ubsan_test.c -lm
ASAN_OPTIONS=detect_leaks=0 build/host/analog-fixed-sweep-strict
cc -O1 -w -g -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -Ibuild/gen -Ifirmware/src -o build/host/analog-fixed-midi-strict tests/midi_control_test.c -lm
ASAN_OPTIONS=detect_leaks=0 build/host/analog-fixed-midi-strict
cc -O1 -w -g -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -Itests -Ibuild/gen -Ifirmware/src -o build/host/analog-fixed-nor-strict /Users/mfaundez/.codex/qa/felucca/fixtures/nrpn-persistence.c -lm
ASAN_OPTIONS=detect_leaks=0 build/host/analog-fixed-nor-strict
node /Users/mfaundez/.codex/qa/felucca/fixtures/nrpn-wasm.mjs
```

Compilación/ejecución exit0 en todos; cero diagnósticos UBSan/ASan en los tres
runs estrictos. NOR: 15 checks, save/load de proyectos/presets/motion desde NOR
simulada y cero writes directos por NRPN. Fixture WASM: 11 checks. La compilación
siempre terminó antes de ejecutar cada binario.

## Comparación target, memoria y pila

Objeto, ELF, app, loader y paquete son **byte-idénticos al baseline NRPN**.
La corrección define el comportamiento en C; la toolchain pi32v2 actual genera
las mismas instrucciones. Esto conserva todos los frames y regiones de aquel
ELF. No es necesario inferir una nueva cota de pila a partir de un frame mayor.

App 496108 B; RAM variables 55060/73728 B (18668 libres); pool 327800/368640 B
(40840 libres); loader 6930 B. Delta de RAM/pool/frames/tamaño:0.
Paquete 610086 B, SHA256 `cbf860b88066f03ab68165aa8a0658eb1465f5cbae75b5d52372899794c50087`.
Objeto `a3b26370b7004ac1632e1b8a2d548023197e5eea0dad3fe8e683c9032c9b6e73`;
ELF `1fa8931a466c5452f9f5c64164555e7f6b354f8ac77e6b38ef869522a1d42d09`.
La identidad del paquete completo conserva también el head de flash y el loader;
no se comparó un offset arbitrario del contenedor.

Se recompiló WASM diagnóstico con exports stack usando flags del informe previo,
versión v1.5.1, `-O2 -ffp-contract=off`, stack 1 MiB/memoria 32 MiB. Comando:

```sh
emcc -O2 -ffp-contract=off -std=gnu99 -w '-DFELUCCA_VERSION="v1.5.1"' -Ibuild/gen -Ifirmware/src --no-entry -sSTANDALONE_WASM -sSTACK_SIZE=1048576 -sINITIAL_MEMORY=33554432 -sFILESYSTEM=0 '-sEXPORTED_FUNCTIONS=["_emscripten_stack_get_base","_emscripten_stack_get_end","_emscripten_stack_get_current","_emscripten_stack_init"]' -o build/analog-fixed-stack.wasm web/emu/felucca_web.c
node /Users/mfaundez/.codex/qa/felucca/fixtures/nrpn-stack-watermark.mjs build/analog-fixed-stack.wasm build/analog-fixed-stack-watermark.json
```

Ambos exit0. Dos patrones reproducen 1114 B en boot/heavy/NRPN y 1984 B tras SAVE,
106988 mensajes/4698 drops por patrón, SP restaurado, memoria sin crecer y audio
finito/no silencioso. Es watermark de bytes escritos de pila C WASM; no cuenta
huecos reservados, pilas VM, ABI/IRQ/contexto target ni rutas no ejercitadas.
**Máximo físico y eficacia de guardas siguen NO CERTIFICADOS.**

## PASS / FAIL esperados / SKIP

- PASS: build, 99 gates ejecutados, strict ANALOG/MIDI/NOR, audio bit-exacto,
  fixtures WASM/stack, identidad target, diffcheck y snapshot sin drift.
- FAIL esperado: baseline estricto, documentado para probar reproducción y
  que los nuevos gates no aceptan ese código. No hay fallos en el fix.
- SKIP: referencia PHYS DaisySP ausente; MENU settings/sender FM6/mapa LEARN
  del editor legacy ausentes; ejecución física USB/TRS/Hapax y stack/IRQ/guards.
- La fixture oficialV15 ya disponible se verificó por SHA256
  `db1642b2b6fa5c2cccb11ffd13878068bb28601678d3644049f99dc40e7edb8a` y permitió
  cerrar aquel SKIP del CLI: restore **simulado** PASS, ningún FM-1 instalado.

Dependencias comprobadas: SDK pins íntegros; Docker 29.8.2, Python 3.14.8,
Pillow 12.3.0, fontTools 4.66.1, Emscripten 6.0.12-git. JieLi 20260730.1 reutilizado.
No se modificaron dependencias, goldens, budgets ni firmware fuera de ANALOG.

Snapshot y hashes en `source-manifest.json`, diff en `source.diff`, test nuevo
archivado por separado. `status.json` conecta artefactos, gates y limitaciones.
La publicación NRPN previa no se utilizó como permiso de commit/push de este
nuevo fix. Checkout principal y rama NRPN quedan intactos. Ningún dispositivo
abierto ni flasheado.


## Evidencia conservada para publicación

Resumen estructurado: [002-analog-ubsan-status.json](002-analog-ubsan-status.json).
Manifest de las fuentes probadas: [002-analog-ubsan-source-manifest.json](002-analog-ubsan-source-manifest.json).
Los logs completos, diff pre-commit y resultados detallados se conservan fuera de `build/` en
`/Users/mfaundez/.codex/qa/felucca/runs/2026-10-12-analog-ubsan-b3fdf11/`.
El diff y el test añadido se incluyen en este commit; no se versionan dependencias ni binarios.
Se volvió a verificar el snapshot de código y todos los artefactos antes de publicar.
